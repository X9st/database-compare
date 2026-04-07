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
  const [starting, setStarting] = useState(false);
  const { current_task, startCompare } = useCompareStore();

  const next = () => {
    if (current === 0 && (!current_task?.source_id || !current_task?.target_id)) {
      message.error('请选择源数据库和目标数据库');
      return;
    }
    if (current === 1) {
      const tableSelection = current_task?.table_selection;
      const mappings = current_task?.options?.table_mappings || [];

      if (tableSelection?.mode === 'include' && (tableSelection.tables || []).length === 0) {
        message.error('请至少选择一张要比对的表');
        return;
      }
      if (tableSelection?.mode === 'mapping') {
        if (mappings.length === 0) {
          message.error('请至少配置一组表映射');
          return;
        }
        const hasInvalidMapping = mappings.some((m) => !m.source_table || !m.target_table);
        if (hasInvalidMapping) {
          message.error('请完善每一组表映射的源表和目标表');
          return;
        }
      }
    }
    setCurrent(current + 1);
  };

  const prev = () => setCurrent(current - 1);

  const handleStart = async () => {
    if (starting) {
      return;
    }
    const options = current_task?.options;
    if (!options) {
      message.error('比对参数缺失');
      return;
    }

    if (options.mode === 'incremental') {
      const inc = options.incremental_config;
      const hasTime = Boolean(inc?.time_column && (inc?.start_time || inc?.end_time));
      const hasBatch = Boolean(inc?.batch_column && inc?.batch_value);
      if (!hasTime && !hasBatch) {
        message.error('增量模式下请至少配置时间条件或批次条件');
        return;
      }
    }

    const pkConfigs = options.table_primary_keys || [];
    const hasInvalidPkConfig = pkConfigs.some((item) => {
      if (!item.source_table) {
        return true;
      }
      if (!item.primary_keys || item.primary_keys.length === 0) {
        return true;
      }
      if (item.target_primary_keys && item.target_primary_keys.length > 0) {
        return item.target_primary_keys.length !== item.primary_keys.length;
      }
      return false;
    });

    if (hasInvalidPkConfig) {
      message.error('业务主键配置不完整，或源/目标主键数量不一致');
      return;
    }

    try {
      setStarting(true);
      message.open({ key: 'compare-start', type: 'loading', content: '正在创建并启动比对任务...' });
      const started = await startCompare();
      setCurrent((prev) => prev + 1);
      if (started.resume_from_task_id) {
        message.success({
          key: 'compare-start',
          content: `已从失败任务 ${started.resume_from_task_id} 断点续跑`,
        });
      } else {
        message.success({ key: 'compare-start', content: '比对任务已启动' });
      }
    } catch (e: any) {
      const errorMsg =
        e?.response?.data?.detail ||
        e?.response?.data?.message ||
        e?.message ||
        '未知错误';
      message.error({ key: 'compare-start', content: `启动失败: ${errorMsg}` });
    } finally {
      setStarting(false);
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
            <Button type="primary" loading={starting} onClick={handleStart}>
              开始比对
            </Button>
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
