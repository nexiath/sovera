#!/usr/bin/env python3
"""
Test script for Sovera API - Table rows functionality
"""

import requests
import json
import time
import os

# Set environment variables
os.environ.update({
    'POSTGRES_SERVER': 'localhost',
    'POSTGRES_USER': 'postgres',
    'POSTGRES_PASSWORD': 'postgres123',
    'POSTGRES_DB': 'sovera',
    'MINIO_ENDPOINT': 'localhost:9000',
    'MINIO_ACCESS_KEY': 'minio',
    'MINIO_SECRET_KEY': 'minio123',
    'SECRET_KEY': 'your-secret-key-here-change-in-production',
    'ALGORITHM': 'HS256',
    'ACCESS_TOKEN_EXPIRE_MINUTES': '30'
})

BASE_URL = 'http://localhost:8000'

def test_complete_workflow():
    print("🚀 Starting Sovera API Test")
    print("=" * 50)
    
    # Generate unique user
    timestamp = int(time.time())
    email = f'test{timestamp}@example.com'
    
    print(f"📧 Testing with email: {email}")
    
    # 1. Register user
    print("\n1️⃣ Registering user...")
    response = requests.post(f'{BASE_URL}/auth/register', json={
        'email': email,
        'password': 'testpass123'
    })
    
    if response.status_code != 200:
        print(f"❌ Register failed: {response.text}")
        return False
    
    print("✅ User registered successfully")
    
    # 2. Login
    print("\n2️⃣ Logging in...")
    response = requests.post(f'{BASE_URL}/auth/login', data={
        'username': email,
        'password': 'testpass123'
    })
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return False
    
    token = response.json()['access_token']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Login successful")
    
    # 3. Create project
    print("\n3️⃣ Creating project...")
    response = requests.post(f'{BASE_URL}/projects/', json={
        'name': 'Test Project API',
        'description': 'Testing table rows API functionality'
    }, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Project creation failed: {response.text}")
        return False
    
    project_data = response.json()
    project_id = project_data['id']
    print(f"✅ Project created with ID: {project_id}")
    
    # 4. Wait for provisioning
    print("\n4️⃣ Waiting for project provisioning...")
    for i in range(20):
        time.sleep(2)
        response = requests.get(f'{BASE_URL}/projects/{project_id}', headers=headers)
        if response.status_code == 200:
            status = response.json().get('provisioning_status')
            print(f"  Status: {status}")
            if status == 'completed':
                print("✅ Project provisioning completed")
                break
            elif status == 'failed':
                print("❌ Project provisioning failed")
                return False
    else:
        print("❌ Provisioning timeout")
        return False
    
    # 5. Create table
    print("\n5️⃣ Creating table...")
    table_schema = {
        'table_name': 'customers',
        'columns': [
            {'name': 'name', 'type': 'VARCHAR', 'length': 100, 'nullable': False},
            {'name': 'email', 'type': 'VARCHAR', 'length': 255, 'nullable': False, 'unique': True},
            {'name': 'age', 'type': 'INTEGER', 'nullable': True},
            {'name': 'active', 'type': 'BOOLEAN', 'nullable': False, 'default': 'true'},
            {'name': 'metadata', 'type': 'JSONB', 'nullable': True}
        ]
    }
    
    response = requests.post(f'{BASE_URL}/projects/{project_id}/tables/', 
                           json=table_schema, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Table creation failed: {response.text}")
        return False
    
    print("✅ Table 'customers' created successfully")
    
    # 6. Test POST /rows - Insert data
    print("\n6️⃣ Testing POST /rows - Insert data...")
    
    test_data = [
        {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': 30,
            'active': True,
            'metadata': {'role': 'admin', 'department': 'IT'}
        },
        {
            'name': 'Jane Smith',
            'email': 'jane@example.com',
            'age': 25,
            'active': True,
            'metadata': {'role': 'user', 'department': 'HR'}
        },
        {
            'name': 'Bob Johnson',
            'email': 'bob@example.com',
            'age': 35,
            'active': False,
            'metadata': {'role': 'user', 'department': 'Finance'}
        }
    ]
    
    inserted_rows = []
    for i, data in enumerate(test_data):
        response = requests.post(f'{BASE_URL}/projects/{project_id}/tables/customers/rows',
                               json=data, headers=headers)
        
        if response.status_code != 200:
            print(f"❌ Row {i+1} insertion failed: {response.text}")
            return False
        
        result = response.json()
        inserted_rows.append(result['data'])
        print(f"✅ Row {i+1} inserted: {data['name']}")
    
    print(f"✅ All {len(test_data)} rows inserted successfully")
    
    # 7. Test GET /rows - Read data
    print("\n7️⃣ Testing GET /rows - Read data...")
    
    response = requests.get(f'{BASE_URL}/projects/{project_id}/tables/customers/rows',
                          headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Read rows failed: {response.text}")
        return False
    
    rows = response.json()
    print(f"✅ Retrieved {len(rows)} rows")
    
    # Display results
    print("\n📊 Retrieved data:")
    for row in rows:
        print(f"  ID: {row['id']}, Name: {row['name']}, Email: {row['email']}, Age: {row['age']}, Active: {row['active']}")
    
    # 8. Test pagination
    print("\n8️⃣ Testing pagination...")
    
    response = requests.get(f'{BASE_URL}/projects/{project_id}/tables/customers/rows?limit=2&offset=0',
                          headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Pagination test failed: {response.text}")
        return False
    
    page_1 = response.json()
    print(f"✅ Page 1 (limit=2): {len(page_1)} rows")
    
    response = requests.get(f'{BASE_URL}/projects/{project_id}/tables/customers/rows?limit=2&offset=2',
                          headers=headers)
    
    if response.status_code == 200:
        page_2 = response.json()
        print(f"✅ Page 2 (limit=2, offset=2): {len(page_2)} rows")
    
    # 9. Test table listing
    print("\n9️⃣ Testing table listing...")
    
    response = requests.get(f'{BASE_URL}/projects/{project_id}/tables/',
                          headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Table listing failed: {response.text}")
        return False
    
    tables = response.json()
    print(f"✅ Found {len(tables)} tables")
    for table in tables:
        print(f"  Table: {table['table_name']}, Columns: {table['column_count']}, Rows: {table['row_count']}")
    
    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! The API is working correctly.")
    print(f"📝 Project ID: {project_id}")
    print(f"🔑 Auth token: {token[:20]}...")
    
    return True

if __name__ == "__main__":
    success = test_complete_workflow()
    if not success:
        print("\n❌ Tests failed!")
        exit(1)
    print("\n✅ All tests completed successfully!")