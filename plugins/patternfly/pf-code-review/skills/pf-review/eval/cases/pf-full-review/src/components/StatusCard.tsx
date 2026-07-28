import React from 'react';
import { Card, CardTitle, CardBody, Label } from '@patternfly/react-core';

interface StatusCardProps {
  title: string;
  status: 'active' | 'inactive' | 'pending';
  message: string;
}

const StatusCard: React.FC<StatusCardProps> = ({ title, status, message }) => {
  const statusColor = status === 'active' ? '#38812f' : status === 'pending' ? '#f0ab00' : '#c9190b';

  return (
    <Card>
      <CardTitle>{title}</CardTitle>
      <CardBody>
        <Label style={{ backgroundColor: statusColor }}>{status}</Label>
        <p style={{ color: '#6a6e73', marginTop: '8px' }}>{message}</p>
      </CardBody>
    </Card>
  );
};

export default StatusCard;
