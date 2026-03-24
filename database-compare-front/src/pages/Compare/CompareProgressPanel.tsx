import React, { useEffect, useState } from 'react';
import { Progress, Button, Result, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useCompareStore } from '@/stores/compareStore';

const { Text } = Typography;

const CompareProgressPanel: React.FC = () => {
  const { taskId, taskStatus } = useCompareStore();
  const navigate = useNavigate();
  const [percent, setPercent] = useState(0);

  useEffect(() => {
    if (taskStatus === 'running') {
      const timer = setInterval(() => {
        setPercent(p => {
          if (p >= 100) {
            clearInterval(timer);
            useCompareStore.setState({ taskStatus: 'completed' });
            return 100;
          }
          return p + 5;
        });
      }, 500);
      return () => clearInterval(timer);
    }
  }, [taskStatus]);

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

  return (
    <div style={{ marginTop: 48, textAlign: 'center' }}>
      <Progress type="circle" percent={percent} size={200} />
      <div style={{ marginTop: 24 }}>
        <Text>正在比对数据，请稍候... ({percent}%)</Text>
      </div>
    </div>
  );
};

export default CompareProgressPanel;
