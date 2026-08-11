import { useCallback, useEffect, useState } from 'react';
import {
  disableScheduler,
  enableScheduler,
  fetchBackendStatus,
  fetchConfig,
  fetchSchedulerStatus,
  fetchSniperRunStatus,
  saveConfig,
  saveSchedulerConfig,
  stopSniperRun,
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

const EMPTY_SCHEDULER = {
  task_name: 'CourtSniper',
  installed: false,
  managed: false,
  enabled: null,
  state: null,
  next_run_time: null,
  last_run_time: null,
  last_run_result: null,
  configuration: null,
  configured: false,
  configuration_in_sync: null,
};

export default function CourtSniperProvider({ children }) {
  const [config, setConfig] = useState({});
  const [sniperRun, setSniperRun] = useState(IDLE_SNIPER_RUN);
  const [scheduler, setScheduler] = useState(EMPTY_SCHEDULER);
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [isLoadingScheduler, setIsLoadingScheduler] = useState(true);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [isSavingScheduler, setIsSavingScheduler] = useState(false);
  const [isTogglingScheduler, setIsTogglingScheduler] = useState(false);
  const [isLaunchingSetup, setIsLaunchingSetup] = useState(false);
  const [isStartingSniper, setIsStartingSniper] = useState(false);
  const [isStoppingSniper, setIsStoppingSniper] = useState(false);
  const [apiError, setApiError] = useState('');
  const [sniperError, setSniperError] = useState('');
  const [schedulerError, setSchedulerError] = useState('');

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([
      fetchBackendStatus(),
      fetchConfig(),
      fetchSniperRunStatus(),
      fetchSchedulerStatus(),
    ]).then(
      ([statusResult, configResult, runResult, schedulerResult]) => {
        if (cancelled) return;

        const isOnline = statusResult.status === 'fulfilled'
          || configResult.status === 'fulfilled'
          || runResult.status === 'fulfilled'
          || schedulerResult.status === 'fulfilled';
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

        if (schedulerResult.status === 'fulfilled') {
          setScheduler(schedulerResult.value || EMPTY_SCHEDULER);
          setSchedulerError('');
        } else {
          setSchedulerError('Unable to load Windows scheduler status.');
        }

        setIsLoadingConfig(false);
        setIsLoadingScheduler(false);
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
      if (['TARGET_HOUR', 'TARGET_MINUTE', 'TARGET_SECOND'].some((key) => key in updates)) {
        setScheduler((current) => (
          current.configured
            ? { ...current, configuration_in_sync: false }
            : current
        ));
      }
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

  const stopActiveSniperRun = useCallback(async () => {
    setIsStoppingSniper(true);
    setSniperError('');
    setSniperRun((current) => (
      current.state === 'running'
        ? { ...current, state: 'stopping' }
        : current
    ));

    try {
      const result = await stopSniperRun();
      setSniperRun(result?.run || IDLE_SNIPER_RUN);
      setConnectionStatus('online');
      return result;
    } catch (error) {
      try {
        const statusResult = await fetchSniperRunStatus();
        setSniperRun(statusResult?.run || IDLE_SNIPER_RUN);
        setConnectionStatus('online');
      } catch {
        setConnectionStatus('offline');
        setSniperRun((current) => (
          current.state === 'stopping'
            ? { ...current, state: 'running' }
            : current
        ));
      }

      setSniperError(error.message || 'Unable to stop CourtSniper.');
      throw error;
    } finally {
      setIsStoppingSniper(false);
    }
  }, []);

  const refreshScheduler = useCallback(async () => {
    setIsLoadingScheduler(true);
    setSchedulerError('');

    try {
      const result = await fetchSchedulerStatus();
      setScheduler(result || EMPTY_SCHEDULER);
      setConnectionStatus('online');
      return result;
    } catch (error) {
      setSchedulerError(error.message || 'Unable to load Windows scheduler status.');
      throw error;
    } finally {
      setIsLoadingScheduler(false);
    }
  }, []);

  const configureSchedule = useCallback(async (scheduleConfig) => {
    setIsSavingScheduler(true);
    setSchedulerError('');

    try {
      const result = await saveSchedulerConfig(scheduleConfig);
      setScheduler(result?.scheduler || EMPTY_SCHEDULER);
      setConnectionStatus('online');
      return result;
    } catch (error) {
      setSchedulerError(error.message || 'Unable to save the Windows schedule.');
      throw error;
    } finally {
      setIsSavingScheduler(false);
    }
  }, []);

  const enableSchedule = useCallback(async () => {
    setIsTogglingScheduler(true);
    setSchedulerError('');

    try {
      const result = await enableScheduler();
      setScheduler(result?.scheduler || EMPTY_SCHEDULER);
      setConnectionStatus('online');
      return result;
    } catch (error) {
      setSchedulerError(error.message || 'Unable to enable future scheduled runs.');
      throw error;
    } finally {
      setIsTogglingScheduler(false);
    }
  }, []);

  const disableSchedule = useCallback(async () => {
    setIsTogglingScheduler(true);
    setSchedulerError('');

    try {
      const result = await disableScheduler();
      setScheduler(result?.scheduler || EMPTY_SCHEDULER);
      setConnectionStatus('online');
      return result;
    } catch (error) {
      setSchedulerError(error.message || 'Unable to disable future scheduled runs.');
      throw error;
    } finally {
      setIsTogglingScheduler(false);
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
        scheduler,
        connectionStatus,
        isLoadingConfig,
        isLoadingScheduler,
        isSavingConfig,
        isSavingScheduler,
        isTogglingScheduler,
        isLaunchingSetup,
        isStartingSniper,
        isStoppingSniper,
        apiError,
        sniperError,
        schedulerError,
        refreshConfiguration,
        updateConfiguration,
        launchSetupSession,
        refreshSniperRun,
        startSniperRun,
        stopActiveSniperRun,
        refreshScheduler,
        configureSchedule,
        enableSchedule,
        disableSchedule,
      }}
    >
      {children}
    </CourtSniperContext.Provider>
  );
}
