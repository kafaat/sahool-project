/**
 * CopilotKit Provider with AG-UI Protocol Integration
 * Provides AI-powered field management capabilities
 */

import React from 'react';
import { CopilotKit } from '@copilotkit/react-core';
import { CopilotSidebar } from '@copilotkit/react-ui';
import '@copilotkit/react-ui/styles.css';

interface CopilotProviderProps {
  children: React.ReactNode;
  runtimeUrl?: string;
}

export const CopilotProvider: React.FC<CopilotProviderProps> = ({
  children,
  runtimeUrl = '/api/copilotkit',
}) => {
  return (
    <CopilotKit runtimeUrl={runtimeUrl}>
      {children}
      <CopilotSidebar
        labels={{
          title: 'Field Assistant',
          initial: 'How can I help you manage your fields today?',
          placeholder: 'Ask about field management...',
        }}
        defaultOpen={false}
        clickOutsideToClose={true}
        instructions={`You are an AI assistant specialized in agricultural field management.
You help users:
- Create and manage field boundaries
- Analyze field data and provide insights
- Split fields into management zones
- Auto-detect field boundaries from satellite imagery
- Provide crop recommendations based on field properties

When users ask about fields, use the available actions to help them.
Always be helpful, concise, and focus on agricultural best practices.`}
      />
    </CopilotKit>
  );
};
