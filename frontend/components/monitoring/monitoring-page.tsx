'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { 
  Activity, 
  Server, 
  Database, 
  HardDrive,
  Cpu,
  MemoryStick,
  Network,
  Clock,
  Loader2,
  Download,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import api from '@/lib/api';

interface SystemInfo {
  hostname: string;
  uptime: string;
  cpu_load: number[];
  ram_usage: {
    total: number;
    available: number;
    percent: number;
    used: number;
  };
  disk_usage: {
    total: number;
    used: number;
    free: number;
    percent: number;
  };
  python_version: string;
  os_version: string;
}

interface PingResult {
  [key: string]: {
    latency_ms: number | null;
    status: string;
  };
}

export function MonitoringPage() {
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [pingResults, setPingResults] = useState<PingResult>({});
  const [logs, setLogs] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [backupLoading, setBackupLoading] = useState(false);

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    try {
      const [systemResponse, pingResponse, logsResponse] = await Promise.all([
        api.getSystemInfo(),
        api.pingHosts(),
        api.getSystemLogs()
      ]);

      if (systemResponse.success && systemResponse.data) {
        setSystemInfo(systemResponse.data);
      }

      if (pingResponse.success && pingResponse.data) {
        setPingResults(pingResponse.data);
      }

      if (logsResponse.success && logsResponse.data) {
        setLogs(logsResponse.data.logs || []);
      }
    } catch (error) {
      toast.error('Erreur lors du chargement des données système');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadSystemData();
    setRefreshing(false);
    toast.success('Données actualisées');
  };

  const handleBackup = async () => {
    setBackupLoading(true);
    try {
      const response = await api.createBackup();
      if (response.success && response.data) {
        if (response.data.download_url) {
          window.open(response.data.download_url, '_blank');
        }
        toast.success('Sauvegarde créée avec succès');
      } else {
        toast.error(response.error || 'Erreur lors de la sauvegarde');
      }
    } catch (error) {
      toast.error('Erreur lors de la sauvegarde');
    } finally {
      setBackupLoading(false);
    }
  };

  const getLogLevelColor = (logLine: string) => {
    if (logLine.includes('ERROR')) {
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100';
    } else if (logLine.includes('WARN')) {
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100';
    } else if (logLine.includes('INFO')) {
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100';
    }
    return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-100';
  };

  const getLogLevel = (logLine: string) => {
    if (logLine.includes('ERROR')) return 'ERROR';
    if (logLine.includes('WARN')) return 'WARN';
    if (logLine.includes('INFO')) return 'INFO';
    return 'LOG';
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Supervision</h1>
          <p className="text-muted-foreground mt-1">
            Surveillez la santé de votre instance Sovera
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Actualiser
          </Button>
          <Button
            onClick={handleBackup}
            disabled={backupLoading}
          >
            {backupLoading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Sauvegarde
          </Button>
        </div>
      </div>

      {/* System Info */}
      {systemInfo && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Server className="h-5 w-5" />
              <span>Informations système</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Hostname</p>
                <p className="font-medium">{systemInfo.hostname}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Uptime</p>
                <p className="font-medium">{systemInfo.uptime}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Python Version</p>
                <p className="font-medium">{systemInfo.python_version}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">OS Version</p>
                <p className="font-medium">{systemInfo.os_version}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* System Stats */}
      {systemInfo && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">CPU</CardTitle>
              <Cpu className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {systemInfo.cpu_load?.length > 0 ? `${systemInfo.cpu_load[0].toFixed(1)}%` : 'N/A'}
              </div>
              <Progress value={systemInfo.cpu_load?.[0] || 0} className="h-2 mt-2" />
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Mémoire</CardTitle>
              <MemoryStick className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemInfo.ram_usage.percent.toFixed(1)}%</div>
              <Progress value={systemInfo.ram_usage.percent} className="h-2 mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {(systemInfo.ram_usage.used / 1024 / 1024 / 1024).toFixed(1)} GB / {(systemInfo.ram_usage.total / 1024 / 1024 / 1024).toFixed(1)} GB
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Disque</CardTitle>
              <HardDrive className="h-4 w-4 text-purple-600" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{systemInfo.disk_usage.percent.toFixed(1)}%</div>
              <Progress value={systemInfo.disk_usage.percent} className="h-2 mt-2" />
              <p className="text-xs text-muted-foreground mt-1">
                {(systemInfo.disk_usage.used / 1024 / 1024 / 1024).toFixed(1)} GB / {(systemInfo.disk_usage.total / 1024 / 1024 / 1024).toFixed(1)} GB
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Network Tests */}
      {Object.keys(pingResults).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Network className="h-5 w-5" />
              <span>Tests de connectivité</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(pingResults).map(([host, result]) => (
                <div key={host} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${result.status === 'up' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <div>
                      <h4 className="font-medium">{host}</h4>
                      <p className="text-sm text-muted-foreground">
                        {result.latency_ms ? `${result.latency_ms}ms` : 'Timeout'}
                      </p>
                    </div>
                  </div>
                  <Badge variant={result.status === 'up' ? 'default' : 'destructive'}>
                    {result.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Clock className="h-5 w-5" />
            <span>Logs récents</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Aucun log</h3>
              <p className="text-muted-foreground">Aucun log disponible</p>
            </div>
          ) : (
            <div className="space-y-2">
              {logs.map((logLine, index) => (
                <div key={index} className="flex items-start space-x-4 p-3 border rounded-lg">
                  <Badge className={getLogLevelColor(logLine)}>
                    {getLogLevel(logLine)}
                  </Badge>
                  <div className="flex-1">
                    <p className="text-sm font-mono">{logLine}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}