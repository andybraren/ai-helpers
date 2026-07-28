import React from 'react';
import { Alert, AlertActionCloseButton } from '@patternfly/react-core';

interface AlertBannerProps {
  title: string;
  variant: 'success' | 'danger' | 'warning' | 'info';
  onClose: () => void;
}

const AlertBanner: React.FC<AlertBannerProps> = ({ title, variant, onClose }) => {
  return (
    <Alert
      variant={variant}
      title={title}
      actionClose={<AlertActionCloseButton onClose={onClose} />}
      style={{ borderLeft: '4px solid #0066cc' }}
    />
  );
};

export default AlertBanner;
