import React, { useState } from 'react';
import { Steps, Button, message, Card } from 'antd';
import { useCompareStore } from '@/stores/compareStore';
import DataSourcePicker from './DataSourcePicker';
import TableSelect from './TableSelect';
import CompareConfig from './CompareConfig';
import CompareProgressPanel from './CompareProgressPanel';
import styles from './index.module.less';

const Compare: React.FC = () => {
  const [current, setCurrent] = useState(0);
  const { currentTask, startCompare } = useCompareStore();

  const next = () => {
    if (current === 0 && (!currentTask?.sourceId || !currentTask?.targetId)) {
      message.error('请选择源数据库和目标数据库');
      return;
    }
    setCurrent(current + 1);
  };

  const prev = () => setCurrent(current - 1);

  const handleStart = async () => {
    try {
      await startCompare();
      setCurrent(current + 1);
      message.success('比对任务已启动');
    } catch (e) {
      message.error('启动失败');
    }
  };

  const steps = [
    { title: '选择数据源', content: <DataSourcePicker /> },
    { title: '选择比对表', content: <TableSelect /> },
    { title: '配置比对选项', content: <CompareConfig /> },
    { title: '执行比对', content: <CompareProgressPanel /> },
  ];

  return (
    <div className={styles.container}>
      <Card bordered={false}>
        <Steps current={current} items={steps.map(item => ({ key: item.title, title: item.title }))} />
        <div className={styles.stepsContent}>{steps[current].content}</div>
        <div className={styles.stepsAction}>
          {current < steps.length - 2 && (
            <Button type="primary" onClick={() => next()}>下一步</Button>
          )}
          {current === steps.length - 2 && (
            <Button type="primary" onClick={handleStart}>开始比对</Button>
          )}
          {current > 0 && current < steps.length - 1 && (
            <Button style={{ margin: '0 8px' }} onClick={() => prev()}>上一步</Button>
          )}
        </div>
      </Card>
    </div>
  );
};

export default Compare;
