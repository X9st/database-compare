import { createHashRouter, Navigate } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import DataSource from '@/pages/DataSource';
import Compare from '@/pages/Compare';
import Result from '@/pages/Result';
import History from '@/pages/History';
import Settings from '@/pages/Settings';

export const router = createHashRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/datasource" replace /> },
      { path: 'datasource', element: <DataSource /> },
      { path: 'compare', element: <Compare /> },
      { path: 'result/:taskId', element: <Result /> },
      { path: 'history', element: <History /> },
      { path: 'settings', element: <Settings /> },
    ],
  },
]);
