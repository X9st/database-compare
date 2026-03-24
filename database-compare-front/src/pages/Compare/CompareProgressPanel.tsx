import React, { useEffect, useState, useCallback } from 'react';
import { Progress, Button, Result, Typography, Space, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCompareStore } from '@/stores/compareStore';
import { compareApi, TaskProgress } from '@/services/compareApi';

const { Text } = Typography;

const CompareProgressPanel: React.FC = () => {
  const { taskId, taskStatus } = useCompareStore();
  const navigate = useNavigate();
  const [progress, setProgress] = useState<TaskProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProgress = useCallback(async () => {
    if (!taskId) return;
    try {
      const response = await compareApi.getProgress(taskId);
      const data = response.data?.data;
      if (data) {
        setProgress(data);
        // 更新全局状态
        if (data.status === 'completed') {
          useCompareStore.setState({ taskStatus: 'completed' });
        } else if (data.status === 'failed') {
          useCompareStore.setState({ taskStatus: 'error' });
          setError(data.errorMessage || '比对失败');
        } else if (data.status === 'paused') {
          useCompareStore.setState({ taskStatus: 'paused' });
        }
      }
    } catch (e) {
      console.error('Failed to fetch progress:', e);
    }
  }, [taskId]);

  useEffect(() => {
    if (taskStatus === 'running' && taskId) {
      // 立即获取一次
      fetchProgress();
      // 轮询进度
      const timer = setInterval(fetchProgress, 2000);
      return () => clearInterval(timer);
    }
  }, [taskStatus, taskId, fetchProgress]);

  const handlePause = async () => {
    if (!taskId) return;
    try {
      await compareApi.pauseTask(taskId);
      useCompareStore.setState({ taskStatus: 'paused' });
    } catch (e) {
      console.error('Failed to pause:', e);
    }
  };

  const handleResume = async () => {
    if (!taskId) return;
    try {
      await compareApi.resumeTask(taskId);
      useCompareStore.setState({ taskStatus: 'running' });
    } catch (e) {
      console.error('Failed to resume:', e);
    }
  };

  const handleStop = async () => {
    if (!taskId) return;
    try {
      await compareApi.stopTask(taskId);
      useCompareStore.setState({ taskStatus: 'idle' });
      useCompareStore.getState().resetTask();
    } catch (e) {
      console.error('Failed to stop:', e);
    }
  };

  // 完成状态
  if (taskStatus === 'completed') {
    return (
      <Result
        status="success"
        title="比对任务执行完成！"
        subTitle={`任务ID: ${taskId}`}
        extra={[
          <Button type="primary" key="result" onClick={() => navigate(`/result/${taskId}`)}>
            查看比对结果
          </Button>,
          <Button key="back" onClick={() => useCompareStore.getState().resetTask()}>
            返回重新配置
          </Button>,
        ]}
      />
    );
  }

  // 错误状态
  if (taskStatus === 'error') {
    return (
      <Result
        status="error"
        title="比对任务失败"
        subTitle={error || '未知错误'}
        extra={[
          <Button type="primary" key="retry" onClick={() => useCompareStore.getState().resetTask()}>
            重新配置
          </Button>,
        ]}
      />
    );
  }

  // 运行/暂停状态
  const percent = progress?.progress || 0;
  const currentTable = progress?.currentTable || '';
  const completedTables = progress?.completedTables || 0;
  const totalTables = progress?.totalTables || 0;
  const elapsedTime = progress?.elapsedTime || '';
  const estimatedRemaining = progress?.estimatedRemaining || '';

  return (
    <div style={{ marginTop: 48, textAlign: 'center' }}>
      <Spin spinning={!progress && taskStatus === 'running'}>
        <Progress type="circle" percent={percent} size={200} />
        <div style={{ marginTop: 24 }}>
          <Text strong>
            {taskStatus === 'paused' ? '已暂停' : '正在比对数据，请稍候...'}
          </Text>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">
              {currentTable && `当前表: ${currentTable}`}
            </Text>
          </div>
          <div style={{ marginTop: 4 }}>
            <Text type="secondary">
              进度: {completedTables} / {totalTables} 表
              {elapsedTime && ` | 已用时: ${elapsedTime}`}
              {estimatedRemaining && ` | 预计剩余: ${estimatedRemaining}`}
            </Text>
          </div>
          <div style={{ marginTop: 24 }}>
            <Space>
              {taskStatus === 'running' && (
                <Button onClick={handlePause}>暂停</Button>
              )}
              {taskStatus === 'paused' && (
                <Button type="primary" onClick={handleResume}>继续</Button>
              )}
              <Button danger onClick={handleStop}>停止</Button>
            </Space>
          </div>
        </div>
      </Spin>
    </div>
  );
};

export default CompareProgressPanel;
