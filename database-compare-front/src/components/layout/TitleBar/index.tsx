import React, { useState, useEffect } from 'react';
import { MinusOutlined, BorderOutlined, CloseOutlined, BlockOutlined } from '@ant-design/icons';
import styles from './index.module.less';
import '@/types/electron'; // 引入类型声明

const TitleBar: React.FC = () => {
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    window.electronAPI?.isMaximized().then(setIsMaximized).catch(() => {});
    window.electronAPI?.onMaximizeChange(setIsMaximized);
  }, []);

  const handleMinimize = () => window.electronAPI?.minimizeWindow();
  const handleMaximize = () => window.electronAPI?.maximizeWindow();
  const handleClose = () => window.electronAPI?.closeWindow();

  return (
    <div className={styles.titleBar}>
      <div className={styles.dragRegion}>
        <span className={styles.title}>数据库比对工具</span>
      </div>
      <div className={styles.controls}>
        <button className={styles.btn} onClick={handleMinimize}>
          <MinusOutlined />
        </button>
        <button className={styles.btn} onClick={handleMaximize}>
          {isMaximized ? <BlockOutlined /> : <BorderOutlined />}
        </button>
        <button className={`${styles.btn} ${styles.closeBtn}`} onClick={handleClose}>
          <CloseOutlined />
        </button>
      </div>
    </div>
  );
};

export default TitleBar;
