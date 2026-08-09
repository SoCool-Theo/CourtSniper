import { useCallback, useEffect, useState } from 'react';
import {
  fetchBackendStatus,
  fetchConfig,
  saveConfig,
  triggerSetupSession,
} from '../api';
import CourtSniperContext from './courtSniperContext';

export default function CourtSniperProvider({ children }) {
  const [config, setConfig] = useState({});
  const [connectionStatus, setConnectionStatus] = useState('checking');
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [isSavingConfig, setIsSavingConfig] = useState(false);
  const [isLaunchingSetup, setIsLaunchingSetup] = useState(false);
  const [apiError, setApiError] = useState('');

  useEffect(() => {
    let cancelled = false;

    Promise.allSettled([fetchBackendStatus(), fetchConfig()]).then(
      ([statusResult, configResult]) => {
        if (cancelled) return;

        const isOnline = statusResult.status === 'fulfilled'
          || configResult.status === 'fulfilled';
        setConnectionStatus(isOnline ? 'online' : 'offline');

        if (configResult.status === 'fulfilled') {
          setConfig(configResult.value || {});
          setApiError('');
        } else {
          setApiError('Unable to load configuration. Start the FastAPI service and try again.');
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

  return (
    <CourtSniperContext.Provider
      value={{
        config,
        connectionStatus,
        isLoadingConfig,
        isSavingConfig,
        isLaunchingSetup,
        apiError,
        refreshConfiguration,
        updateConfiguration,
        launchSetupSession,
      }}
    >
      {children}
    </CourtSniperContext.Provider>
  );
}
