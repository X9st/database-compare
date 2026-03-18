import React, { useState, useEffect } from 'react'

function ComparisonTask({ onComplete }) {
  const [connections, setConnections] = useState([])
  const [sourceConn, setSourceConn] = useState('')
  const [targetConn, setTargetConn] = useState('')
  const [tables, setTables] = useState([])
  const [selectedTables, setSelectedTables] = useState([])
  const [compareOptions, setCompareOptions] = useState({
    structure: true,
    columns: true,
    data: false
  })
  const [isLoading, setIsLoading] = useState(false)
  const [taskStatus, setTaskStatus] = useState(null)
  const [useTableMapping, setUseTableMapping] = useState(false)
  const [tableMapping, setTableMapping] = useState({ source: '', target: '' })

  useEffect(() => {
    loadConnections()
  }, [])

  const loadConnections = async () => {
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.getConnections()
        if (result.success) {
          setConnections(result.connections)
        }
      }
    } catch (error) {
      console.error('加载连接失败:', error)
    }
  }

  const loadTables = async (connectionId) => {
    try {
      const conn = connections.find(c => c.id === connectionId)
      if (!conn) return

      setIsLoading(true)
      
      if (window.electronAPI && window.electronAPI.getConnectionFull) {
        // 获取完整连接信息（包含密码）
        const fullResult = await window.electronAPI.getConnectionFull(connectionId)
        if (!fullResult.success || !fullResult.connection) {
          alert('获取连接信息失败')
          setIsLoading(false)
          return
        }
        
        const fullConn = fullResult.connection
        
        // 调用后端获取表列表
        const result = await window.electronAPI.getDatabaseTables({
          type: fullConn.type,
          host: fullConn.host,
          port: fullConn.port,
          database: fullConn.database,
          username: fullConn.username,
          password: fullConn.password
        })
        
        if (result.success) {
          setTables(result.tables || [])
        } else {
          alert('获取表列表失败: ' + result.message)
        }
      } else {
        // 开发模式：使用模拟数据
        setTimeout(() => {
          setTables([
            { name: 'users', comment: '用户表' },
            { name: 'orders', comment: '订单表' },
            { name: 'products', comment: '产品表' }
          ])
        }, 500)
      }
    } catch (error) {
      console.error('加载表列表失败:', error)
      alert('加载表列表失败: ' + error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSourceChange = (e) => {
    const value = e.target.value
    setSourceConn(value)
    if (value) {
      loadTables(value, true)
    }
  }

  const handleTargetChange = (e) => {
    setTargetConn(e.target.value)
  }

  const toggleTable = (tableName) => {
    setSelectedTables(prev => 
      prev.includes(tableName)
        ? prev.filter(t => t !== tableName)
        : [...prev, tableName]
    )
  }

  const toggleAllTables = () => {
    if (selectedTables.length === tables.length) {
      setSelectedTables([])
    } else {
      setSelectedTables(tables.map(t => t.name))
    }
  }

  const handleOptionChange = (option) => {
    setCompareOptions(prev => ({
      ...prev,
      [option]: !prev[option]
    }))
  }

  const startComparison = async () => {
    if (!sourceConn || !targetConn) {
      alert('请选择源数据库和目标数据库')
      return
    }

    // 检查表选择
    if (useTableMapping) {
      if (!tableMapping.source || !tableMapping.target) {
        alert('请输入源表名和目标表名')
        return
      }
    } else {
      if (selectedTables.length === 0) {
        alert('请至少选择一个要比对的表')
        return
      }
    }

    setTaskStatus('running')
    
    try {
      if (window.electronAPI) {
        // 获取完整的连接信息
        const [sourceResult, targetResult] = await Promise.all([
          window.electronAPI.getConnectionFull(sourceConn),
          window.electronAPI.getConnectionFull(targetConn)
        ])
        
        if (!sourceResult.success || !targetResult.success) {
          alert('获取连接信息失败')
          setTaskStatus('error')
          return
        }
        
        // 准备比对参数
        const compareParams = {
          source: {
            type: sourceResult.connection.type,
            host: sourceResult.connection.host,
            port: sourceResult.connection.port,
            database: sourceResult.connection.database,
            username: sourceResult.connection.username,
            password: sourceResult.connection.password
          },
          target: {
            type: targetResult.connection.type,
            host: targetResult.connection.host,
            port: targetResult.connection.port,
            database: targetResult.connection.database,
            username: targetResult.connection.username,
            password: targetResult.connection.password
          },
          options: compareOptions
        }
        
        // 如果使用表名映射
        if (useTableMapping) {
          compareParams.table_mapping = {
            [tableMapping.source]: tableMapping.target
          }
        } else {
          compareParams.tables = selectedTables
        }
        
        // 调用后端开始比对
        const result = await window.electronAPI.startComparison(compareParams)
        
        if (result.success) {
          // 开始轮询任务进度
          pollTaskProgress(result.task_id)
        } else {
          alert('启动比对失败: ' + result.message)
          setTaskStatus('error')
        }
      } else {
        // 开发模式：模拟比对
        setTimeout(() => {
          setTaskStatus('completed')
        }, 3000)
      }
    } catch (error) {
      console.error('启动比对失败:', error)
      alert('启动比对失败: ' + error.message)
      setTaskStatus('error')
    }
  }

  const pollTaskProgress = async (taskId) => {
    const checkProgress = async () => {
      try {
        const result = await window.electronAPI.getComparisonProgress(taskId)
        
        if (result.status === 'completed') {
          setTaskStatus('completed')
          // 获取比对结果
          const resultData = await window.electronAPI.getComparisonResult(taskId)
          console.log('比对结果:', resultData)
          
          // 调用回调函数，传递结果
          if (onComplete && resultData.success) {
            onComplete(taskId, resultData.result)
          }
        } else if (result.status === 'error') {
          setTaskStatus('error')
        } else {
          // 继续轮询
          setTimeout(checkProgress, 1000)
        }
      } catch (error) {
        console.error('获取进度失败:', error)
        setTaskStatus('error')
      }
    }
    
    checkProgress()
  }

  return (
    <div className="comparison-task">
      <div className="section-header">
        <h2>新建比对任务</h2>
      </div>

      <div className="comparison-form">
        {/* 数据源选择 */}
        <div className="form-section">
          <h3>1. 选择数据源</h3>
          <div className="connection-selectors">
            <div className="form-group">
              <label>源数据库</label>
              <select value={sourceConn} onChange={handleSourceChange}>
                <option value="">请选择...</option>
                {connections.map(conn => (
                  <option key={conn.id} value={conn.id}>
                    {conn.name} ({conn.type})
                  </option>
                ))}
              </select>
            </div>
            
            <div className="arrow">→</div>
            
            <div className="form-group">
              <label>目标数据库</label>
              <select value={targetConn} onChange={handleTargetChange}>
                <option value="">请选择...</option>
                {connections.map(conn => (
                  <option key={conn.id} value={conn.id}>
                    {conn.name} ({conn.type})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* 表选择模式切换 */}
        <div className="form-section">
          <h3>2. 选择比对方式</h3>
          <div className="compare-mode-selector">
            <label className="mode-option">
              <input
                type="radio"
                name="compareMode"
                checked={!useTableMapping}
                onChange={() => setUseTableMapping(false)}
              />
              <span>多表比对（从列表选择）</span>
            </label>
            <label className="mode-option">
              <input
                type="radio"
                name="compareMode"
                checked={useTableMapping}
                onChange={() => setUseTableMapping(true)}
              />
              <span>指定表比对（表名可不同）</span>
            </label>
          </div>
        </div>

        {/* 表名映射输入 */}
        {useTableMapping && (
          <div className="form-section">
            <h3>指定要比对的表</h3>
            <div className="table-mapping-inputs">
              <div className="form-group">
                <label>源表名</label>
                <input
                  type="text"
                  value={tableMapping.source}
                  onChange={(e) => setTableMapping(prev => ({ ...prev, source: e.target.value }))}
                  placeholder="例如：users"
                />
              </div>
              <div className="arrow">→</div>
              <div className="form-group">
                <label>目标表名</label>
                <input
                  type="text"
                  value={tableMapping.target}
                  onChange={(e) => setTableMapping(prev => ({ ...prev, target: e.target.value }))}
                  placeholder="例如：users_new"
                />
              </div>
            </div>
            <p className="mapping-hint">
              支持比对不同名称的表，例如：db1.users 和 db2.user_backup
            </p>
          </div>
        )}

        {/* 表选择 */}
        {!useTableMapping && tables.length > 0 && (
          <div className="form-section">
            <h3>选择要比对的表</h3>
            <div className="table-selection">
              <label className="checkbox-all">
                <input
                  type="checkbox"
                  checked={selectedTables.length === tables.length}
                  onChange={toggleAllTables}
                />
                全选 ({selectedTables.length}/{tables.length})
              </label>
              
              <div className="tables-grid">
                {tables.map(table => (
                  <label key={table.name} className="table-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedTables.includes(table.name)}
                      onChange={() => toggleTable(table.name)}
                    />
                    <span className="table-name">{table.name}</span>
                    {table.comment && (
                      <span className="table-comment">{table.comment}</span>
                    )}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* 比对选项 */}
        <div className="form-section">
          <h3>3. 配置比对选项</h3>
          <div className="compare-options">
            <label className="option-checkbox">
              <input
                type="checkbox"
                checked={compareOptions.structure}
                onChange={() => handleOptionChange('structure')}
              />
              <div className="option-info">
                <span className="option-title">表结构比对</span>
                <span className="option-desc">比对表名、表注释、存储引擎等</span>
              </div>
            </label>
            
            <label className="option-checkbox">
              <input
                type="checkbox"
                checked={compareOptions.columns}
                onChange={() => handleOptionChange('columns')}
              />
              <div className="option-info">
                <span className="option-title">字段信息比对</span>
                <span className="option-desc">比对字段名、类型、长度、是否可空等</span>
              </div>
            </label>
            
            <label className="option-checkbox">
              <input
                type="checkbox"
                checked={compareOptions.data}
                onChange={() => handleOptionChange('data')}
              />
              <div className="option-info">
                <span className="option-title">数据内容比对</span>
                <span className="option-desc">比对记录数量和数据一致性（较慢）</span>
              </div>
            </label>
          </div>
        </div>

        {/* 执行按钮 */}
        <div className="form-actions">
          <button 
            className="btn-primary btn-large"
            onClick={startComparison}
            disabled={taskStatus === 'running'}
          >
            {taskStatus === 'running' ? '比对中...' : '开始比对'}
          </button>
        </div>

        {/* 任务状态 */}
        {taskStatus && (
          <div className={`task-status ${taskStatus}`}>
            {taskStatus === 'running' && '正在执行比对任务...'}
            {taskStatus === 'completed' && '比对完成！请查看结果页面'}
            {taskStatus === 'error' && '比对失败，请检查配置'}
          </div>
        )}
      </div>
    </div>
  )
}

export default ComparisonTask
