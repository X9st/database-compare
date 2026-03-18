import React, { useState } from 'react'

function ResultDisplay({ taskId, resultData }) {
  const [activeTab, setActiveTab] = useState('overview')
  const [exporting, setExporting] = useState(false)
  
  // 使用传入的真实数据或模拟数据
  const result = resultData || {
    summary: {
      totalTables: 10,
      addedTables: 2,
      removedTables: 1,
      modifiedTables: 3,
      addedColumns: 5,
      removedColumns: 2,
      modifiedColumns: 8
    },
    tableDiffs: [
      {
        type: 'added',
        name: 'new_users',
        info: { comment: '新用户表', engine: 'InnoDB' }
      },
      {
        type: 'removed',
        name: 'old_logs',
        info: { comment: '旧日志表', engine: 'MyISAM' }
      },
      {
        type: 'modified',
        name: 'orders',
        differences: [
          { field: 'comment', source: '订单表', target: '订单信息表' }
        ]
      }
    ],
    columnDiffs: {
      'users': {
        added: [{ name: 'phone', type: 'varchar', max_length: 20 }],
        removed: [{ name: 'fax', type: 'varchar', max_length: 20 }],
        modified: [
          {
            name: 'email',
            differences: [
              { field: 'max_length', source: 50, target: 100 }
            ]
          }
        ]
      }
    }
  }

  const handleExport = async (format) => {
    if (!taskId) {
      alert('没有可导出的任务')
      return
    }
    
    setExporting(true)
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.exportReport(taskId, format)
        if (result.success) {
          alert(`报告已导出: ${result.filename}`)
        } else {
          alert('导出失败: ' + result.message)
        }
      } else {
        alert('开发模式：导出功能需要 Electron 环境')
      }
    } catch (error) {
      console.error('导出失败:', error)
      alert('导出失败: ' + error.message)
    } finally {
      setExporting(false)
    }
  }

  const renderOverview = () => (
    <div className="result-overview">
      <div className="summary-cards">
        <div className="summary-card added">
          <h4>新增</h4>
          <div className="stats">
            <div className="stat">
              <span className="number">{result.summary?.addedTables || 0}</span>
              <span className="label">表</span>
            </div>
            <div className="stat">
              <span className="number">{result.summary?.addedColumns || 0}</span>
              <span className="label">字段</span>
            </div>
          </div>
        </div>
        
        <div className="summary-card removed">
          <h4>删除</h4>
          <div className="stats">
            <div className="stat">
              <span className="number">{result.summary?.removedTables || 0}</span>
              <span className="label">表</span>
            </div>
            <div className="stat">
              <span className="number">{result.summary?.removedColumns || 0}</span>
              <span className="label">字段</span>
            </div>
          </div>
        </div>
        
        <div className="summary-card modified">
          <h4>修改</h4>
          <div className="stats">
            <div className="stat">
              <span className="number">{result.summary?.modifiedTables || 0}</span>
              <span className="label">表</span>
            </div>
            <div className="stat">
              <span className="number">{result.summary?.modifiedColumns || 0}</span>
              <span className="label">字段</span>
            </div>
          </div>
        </div>
      </div>

      <div className="export-section">
        <h4>导出报告</h4>
        <div className="export-buttons">
          <button 
            className="btn-secondary" 
            onClick={() => handleExport('html')}
            disabled={exporting || !taskId}
          >
            {exporting ? '导出中...' : '导出 HTML'}
          </button>
          <button 
            className="btn-secondary" 
            onClick={() => handleExport('excel')}
            disabled={exporting || !taskId}
          >
            {exporting ? '导出中...' : '导出 Excel'}
          </button>
        </div>
      </div>
    </div>
  )

  const renderTableDiffs = () => (
    <div className="table-diffs">
      <h4>表结构差异</h4>
      <div className="diff-list">
        {result.tableDiffs?.map((diff, index) => (
          <div key={index} className={`diff-item ${diff.type}`}>
            <div className="diff-header">
              <span className={`diff-badge ${diff.type}`}>
                {diff.type === 'added' && '新增'}
                {diff.type === 'removed' && '删除'}
                {diff.type === 'modified' && '修改'}
              </span>
              <span className="diff-name">{diff.name}</span>
            </div>
            
            {diff.type === 'modified' && diff.differences && (
              <div className="diff-details">
                {diff.differences.map((d, i) => (
                  <div key={i} className="detail-row">
                    <span className="field">{d.field}:</span>
                    <span className="source">{d.source}</span>
                    <span className="arrow">→</span>
                    <span className="target">{d.target}</span>
                  </div>
                ))}
              </div>
            )}
            
            {diff.info && (
              <div className="diff-info">
                {diff.info.comment && <span>注释: {diff.info.comment}</span>}
                {diff.info.engine && <span>引擎: {diff.info.engine}</span>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )

  const renderColumnDiffs = () => (
    <div className="column-diffs">
      <h4>字段差异</h4>
      {result.columnDiffs && Object.entries(result.columnDiffs).map(([tableName, diffs]) => (
        <div key={tableName} className="table-column-diff">
          <h5>表: {tableName}</h5>
          
          {diffs.added?.length > 0 && (
            <div className="diff-section">
              <h6>新增字段</h6>
              {diffs.added.map((col, i) => (
                <div key={i} className="diff-row added">
                  <span className="col-name">{col.name}</span>
                  <span className="col-type">{col.type}({col.max_length})</span>
                </div>
              ))}
            </div>
          )}
          
          {diffs.removed?.length > 0 && (
            <div className="diff-section">
              <h6>删除字段</h6>
              {diffs.removed.map((col, i) => (
                <div key={i} className="diff-row removed">
                  <span className="col-name">{col.name}</span>
                  <span className="col-type">{col.type}({col.max_length})</span>
                </div>
              ))}
            </div>
          )}
          
          {diffs.modified?.length > 0 && (
            <div className="diff-section">
              <h6>修改字段</h6>
              {diffs.modified.map((col, i) => (
                <div key={i} className="diff-row modified">
                  <span className="col-name">{col.name}</span>
                  {col.differences.map((d, j) => (
                    <span key={j} className="col-change">
                      {d.field}: {d.source} → {d.target}
                    </span>
                  ))}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )

  return (
    <div className="result-display">
      <div className="section-header">
        <h2>比对结果</h2>
      </div>

      <div className="result-tabs">
        <button 
          className={activeTab === 'overview' ? 'active' : ''}
          onClick={() => setActiveTab('overview')}
        >
          概览
        </button>
        <button 
          className={activeTab === 'tables' ? 'active' : ''}
          onClick={() => setActiveTab('tables')}
        >
          表结构差异
        </button>
        <button 
          className={activeTab === 'columns' ? 'active' : ''}
          onClick={() => setActiveTab('columns')}
        >
          字段差异
        </button>
        <button 
          className={activeTab === 'data' ? 'active' : ''}
          onClick={() => setActiveTab('data')}
        >
          数据差异
        </button>
      </div>

      <div className="result-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'tables' && renderTableDiffs()}
        {activeTab === 'columns' && renderColumnDiffs()}
        {activeTab === 'data' && (
          <div className="data-diffs">
            <p>数据差异功能开发中...</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default ResultDisplay
