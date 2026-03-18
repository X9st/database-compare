import React, { useState, useEffect } from 'react'

const DB_TYPES = [
  { value: 'mysql', label: 'MySQL / MariaDB' },
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'sqlite', label: 'SQLite' },
  { value: 'dameng', label: '达梦数据库 (DM)', port: 5236 },
  { value: 'inceptor', label: 'Inceptor (星环)', port: 10000 },
  { value: 'kingbase', label: '人大金仓 (Kingbase)', port: 54321 },
]

function ConnectionManager() {
  const [connections, setConnections] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    type: 'mysql',
    host: 'localhost',
    port: 3306,
    database: '',
    username: '',
    password: ''
  })
  const [testStatus, setTestStatus] = useState(null)

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

  const handleInputChange = (e) => {
    const { name, value } = e.target
    
    if (name === 'type') {
      // 切换数据库类型时，自动设置默认端口
      const dbType = DB_TYPES.find(t => t.value === value)
      setFormData(prev => ({
        ...prev,
        type: value,
        port: dbType?.port || (value === 'mysql' ? 3306 : value === 'postgresql' ? 5432 : '')
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: name === 'port' ? parseInt(value) || '' : value
      }))
    }
  }

  const testConnection = async () => {
    setTestStatus('testing')
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.testDatabaseConnection(formData)
        setTestStatus(result.success ? 'success' : 'error')
      } else {
        setTestStatus('development')
      }
    } catch (error) {
      setTestStatus('error')
    }
  }

  const saveConnection = async () => {
    try {
      if (window.electronAPI) {
        await window.electronAPI.saveConnection(formData)
        setShowForm(false)
        setFormData({
          name: '',
          type: 'mysql',
          host: 'localhost',
          port: 3306,
          database: '',
          username: '',
          password: ''
        })
        loadConnections()
      }
    } catch (error) {
      console.error('保存连接失败:', error)
    }
  }

  const deleteConnection = async (id) => {
    if (!confirm('确定要删除这个连接吗？')) {
      return
    }
    
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.deleteConnection(id)
        if (result.success) {
          loadConnections()
        } else {
          alert('删除失败: ' + result.message)
        }
      }
    } catch (error) {
      console.error('删除连接失败:', error)
      alert('删除失败: ' + error.message)
    }
  }

  return (
    <div className="connection-manager">
      <div className="section-header">
        <h2>数据库连接管理</h2>
        <button className="btn-primary" onClick={() => setShowForm(true)}>
          + 新建连接
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay">
          <div className="modal">
            <h3>新建数据库连接</h3>
            
            <div className="form-group">
              <label>连接名称</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                placeholder="例如：生产环境 MySQL"
              />
            </div>

            <div className="form-group">
              <label>数据库类型</label>
              <select name="type" value={formData.type} onChange={handleInputChange}>
                {DB_TYPES.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            {formData.type !== 'sqlite' && (
              <>
                <div className="form-row">
                  <div className="form-group">
                    <label>主机地址</label>
                    <input
                      type="text"
                      name="host"
                      value={formData.host}
                      onChange={handleInputChange}
                    />
                  </div>
                  <div className="form-group">
                    <label>端口</label>
                    <input
                      type="number"
                      name="port"
                      value={formData.port}
                      onChange={handleInputChange}
                    />
                  </div>
                </div>
              </>
            )}

            <div className="form-group">
              <label>数据库名</label>
              <input
                type="text"
                name="database"
                value={formData.database}
                onChange={handleInputChange}
              />
            </div>

            {formData.type !== 'sqlite' && (
              <>
                <div className="form-group">
                  <label>用户名</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                  />
                </div>
                <div className="form-group">
                  <label>密码</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                  />
                </div>
              </>
            )}

            <div className="form-actions">
              <button 
                className="btn-secondary" 
                onClick={testConnection}
                disabled={testStatus === 'testing'}
              >
                {testStatus === 'testing' ? '测试中...' : '测试连接'}
              </button>
              <button className="btn-primary" onClick={saveConnection}>
                保存
              </button>
              <button className="btn-text" onClick={() => setShowForm(false)}>
                取消
              </button>
            </div>

            {testStatus && testStatus !== 'testing' && (
              <div className={`test-result ${testStatus}`}>
                {testStatus === 'success' && '连接测试成功！'}
                {testStatus === 'error' && '连接测试失败，请检查配置。'}
                {testStatus === 'development' && '开发模式：无法测试连接'}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="connections-list">
        {connections.length === 0 ? (
          <div className="empty-state">
            <p>暂无数据库连接</p>
            <p>点击"新建连接"添加数据库配置</p>
          </div>
        ) : (
          connections.map(conn => (
            <div key={conn.id} className="connection-card">
              <div className="connection-info">
                <h4>{conn.name}</h4>
                <p className="connection-type">
                  {DB_TYPES.find(t => t.value === conn.type)?.label || conn.type}
                </p>
                <p className="connection-detail">
                  {conn.host}:{conn.port}/{conn.database}
                </p>
              </div>
              <div className="connection-actions">
                <button 
                  className="btn-icon"
                  onClick={() => deleteConnection(conn.id)}
                  title="删除"
                >
                  🗑️
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}

export default ConnectionManager
