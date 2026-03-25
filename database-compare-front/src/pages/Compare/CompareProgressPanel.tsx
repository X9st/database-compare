import React, { useEffect, useState, useCallback } from 'react';
import { Progress, Button, Result, Typography, Space, Spin } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCompareStore } from '@/stores/compareStore';
import { compareApi, TaskStatusResponse } from '@/services/compareApi';

const { Text } = Typography;

const CompareProgressPanel: React.FC = () => {
  const { task_id, task_status, result_id } = useCompareStore();
  const navigate = useNavigate();
  const [progress, setProgress] = useState<TaskStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProgress = useCallback(async () => {
    if (!task_id) {
      return;
    }
    try {
      const response = await compareApi.getProgress(task_id);
      const data = response.data?.data;
      if (data) {
        setProgress(data);
        if (data.status === 'completed') {
          useCompareStore.setState({ task_status: 'completed', result_id: data.result_id || null });
        } else if (data.status === 'failed') {
          useCompareStore.setState({ task_status: 'error' });
          setError(data.error_message || '比对失败');
        } else if (data.status === 'paused') {
          useCompareStore.setState({ task_status: 'paused' });
        } else if (data.status === 'running') {
          useCompareStore.setState({ task_status: 'running' });
        }
      }
    } catch (e) {
      console.error('Failed to fetch progress:', e);
    }
  }, [task_id]);

  useEffect(() => {
    if (task_status === 'running' && task_id) {
      fetchProgress();
      const timer = setInterval(fetchProgress, 2000);
      return () => clearInterval(timer);
    }
  }, [task_status, task_id, fetchProgress]);

  const handlePause = async () => {
    if (!task_id) {
      return;
    }
    try {
      await compareApi.pauseTask(task_id);
      useCompareStore.setState({ task_status: 'paused' });
    } catch (e) {
      console.error('Failed to pause:', e);
    }
  };

  const handleResume = async () => {
    if (!task_id) {
      return;
    }
    try {
      await compareApi.resumeTask(task_id);
      useCompareStore.setState({ task_status: 'running' });
    } catch (e) {
      console.error('Failed to resume:', e);
    }
  };

  const handleStop = async () => {
    if (!task_id) {
      return;
    }
    try {
      await compareApi.stopTask(task_id);
      useCompareStore.setState({ task_status: 'idle' });
      useCompareStore.getState().resetTask();
    } catch (e) {
      console.error('Failed to stop:', e);
    }
  };

  if (task_status === 'completed') {
    const final_result_id = result_id || progress?.result_id;
    return (
      <Result
        status="success"
        title="比对任务执行完成！"
        subTitle={`任务ID: ${task_id}`}
        extra={[
          <Button
            type="primary"
            key="result"
            disabled={!final_result_id}
            onClick={() => final_result_id && navigate(`/result/${final_result_id}`)}
          >
            查看比对结果
          </Button>,
          <Button key="back" onClick={() => useCompareStore.getState().resetTask()}>
            返回重新配置
          </Button>,
        ]}
      />
    );
  }

  if (task_status === 'error') {
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

  const percent = progress?.progress?.percentage || 0;
  const current_table = progress?.progress?.current_table || '';
  const completed_tables = progress?.progress?.completed_tables || 0;
  const total_tables = progress?.progress?.total_tables || 0;
  const elapsed_seconds = progress?.progress?.elapsed_seconds || 0;
  const estimated_remaining_seconds = progress?.progress?.estimated_remaining_seconds;

  return (
    <div style={{ marginTop: 48, textAlign: 'center' }}>
      <Spin spinning={!progress && task_status === 'running'}>
        <Progress type="circle" percent={percent} size={200} />
        <div style={{ marginTop: 24 }}>
          <Text strong>
            {task_status === 'paused' ? '已暂停' : '正在比对数据，请稍候...'}
          </Text>
          <div style={{ marginTop: 8 }}>
            <Text type="secondary">
              {current_table && `当前表: ${current_table}`}
            </Text>
          </div>
          <div style={{ marginTop: 4 }}>
            <Text type="secondary">
              进度: {completed_tables} / {total_tables} 表
              {elapsed_seconds > 0 && ` | 已用时: ${elapsed_seconds}s`}
              {estimated_remaining_seconds !== undefined && ` | 预计剩余: ${estimated_remaining_seconds}s`}
            </Text>
          </div>
          <div style={{ marginTop: 24 }}>
            <Space>
              {task_status === 'running' && (
                <Button onClick={handlePause}>暂停</Button>
              )}
              {task_status === 'paused' && (
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
