import { useCallback, useEffect, useState } from 'react';
import {
  fetchBackendStatus,
  fetchConfig,
  fetchSniperRunStatus,
  saveConfig,
  triggerSetupSession,
  triggerSniperRun,
} from '../api';
import CourtSniperContext from './courtSniperContext';

const IDLE_SNIPER_RUN = {
  state: 'idle',
  pid: null,
  started_at: null,
  finished_at: null,
  exit_code: null,
};

export default function CourtSniperProvider({ children }) {
  const [config, setConfig] = useState({});
  const [sniperRun, setSniperRun] = useState(IDLE_SNIPER_RUN);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [isLaunchingSetup, setIsLaunchingSetup] = useState(false);
  const [isStartingSniper, setIsStartingSniper] = useState(false);
  const [apiError, setApiError] = useState('');
  const [sniperError, setSniperError] = useState('');

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([
      fetchBackendStatus(),
      fetchConfig(),
      fetchSniperRunStatus(),
    ]).then(
      ([statusResult, configResult, runResult]) => {
        if (cancelled) return;

        const isOnline = statusResult.status === 'fulfilled'
          || configResult.status === 'fulfilled'
          || runResult.status === 'fulfilled';
        setConnectionStatus(isOnline ? 'online' : 'offline');

        if (configResult.status === 'fulfilled') {
          setConfig(configResult.value || {});
          setApiError('');
        } else {
          setApiError('Unable to load configuration. Start the FastAPI service and try again.');
        }

        if (runResult.status === 'fulfilled') {
          setSniperRun(runResult.value?.run || IDLE_SNIPER_RUN);
        }

        setIsLoadingConfig(false);
      },
    );

    return () => {
      cancelled = true;
    };
  }, []);

  const refreshConfiguration = useCallback(async () => {
    setIsLoadingConfig(true);
    setApiError('');

    try {
      const nextConfig = await fetchConfig();
      setConfig(nextConfig || {});
      setConnectionStatus('online');
      return nextConfig;
    } catch (error) {
      setConnectionStatus('offline');
      setApiError(error.message || 'Unable to refresh configuration.');
      throw error;
    } finally {
      setIsLoadingConfig(false);
    }
  }, []);

  const updateConfiguration = useCallback(async (updates) => {
    setIsSavingConfig(true);
    setApiError('');

    try {
      const result = await saveConfig(updates);
      setConfig((current) => ({ ...current, ...updates }));
      setConnectionStatus('online');
      return result;
    } catch (error) {
      setConnectionStatus('offline');
      setApiError(error.message || 'Unable to save configuration.');
      throw error;
    } finally {
      setIsSavingConfig(false);
    }
  }, []);

  const launchSetupSession = useCallback(async () => {
    setIsLaunchingSetup(true);
    setApiError('');

    try {
      const result = await triggerSetupSession();
      setConnectionStatus('online');
      return result;
    } catch (error) {
      setConnectionStatus('offline');
      setApiError(error.message || 'Unable to open the login browser.');
      throw error;
    } finally {
      setIsLaunchingSetup(false);
    }
  }, []);

  const refreshSniperRun = useCallback(async () => {
    try {
      const result = await fetchSniperRunStatus();
      setSniperRun(result?.run || IDLE_SNIPER_RUN);
      setConnectionStatus('online');
      setSniperError('');
      return result?.run;
    } catch (error) {
      setConnectionStatus('offline');
      setSniperError(error.message || 'Unable to load sniper run status.');
      throw error;
    }
  }, []);

  const startSniperRun = useCallback(async () => {
    setIsStartingSniper(true);
    setSniperError('');

    try {
      const result = await triggerSniperRun();
      setSniperRun(result?.run || IDLE_SNIPER_RUN);
      setConnectionStatus('online');
      return result;
    } catch (error) {
      setSniperError(error.message || 'Unable to start CourtSniper.');
      throw error;
    } finally {
      setIsStartingSniper(false);
    }
  }, []);

  useEffect(() => {
    if (sniperRun.state !== 'running') return undefined;

    let cancelled = false;
    const intervalId = window.setInterval(async () => {
      try {
        const result = await fetchSniperRunStatus();
        if (cancelled) return;

        setSniperRun(result?.run || IDLE_SNIPER_RUN);
        setConnectionStatus('online');
        setSniperError('');
      } catch (error) {
        if (cancelled) return;

        setConnectionStatus('offline');
        setSniperError(error.message || 'Unable to load sniper run status.');
      }
    }, 1000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [sniperRun.state]);

  return (
    <CourtSniperContext.Provider
      value={{
        config,
        sniperRun,
        connectionStatus,
        isLoadingConfig,
        isSavingConfig,
        isLaunchingSetup,
        isStartingSniper,
        apiError,
        sniperError,
        refreshConfiguration,
        updateConfiguration,
        launchSetupSession,
        refreshSniperRun,
        startSniperRun,
      }}
    >
      {children}
    </CourtSniperContext.Provider>
  );
}
