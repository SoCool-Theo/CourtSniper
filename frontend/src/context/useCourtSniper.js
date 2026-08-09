import { useContext } from 'react';
import CourtSniperContext from './courtSniperContext';

export default function useCourtSniper() {
  const context = useContext(CourtSniperContext);

  if (!context) {
    throw new Error('useCourtSniper must be used inside CourtSniperProvider.');
  }

  return context;
}
