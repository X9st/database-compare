import React, { useState, useEffect } from 'react'
import ConnectionManager from './components/ConnectionManager'
import ComparisonTask from './components/ComparisonTask'
import ResultDisplay from './components/ResultDisplay'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('connections')
  const [pythonStatus, setPythonStatus] = useState('checking')
  const [currentResult, setCurrentResult] = useState(null)
  const [currentTaskId, setCurrentTaskId] = useState(null)
  const [taskHistory, setTaskHistory] = useState([])

  useEffect(() => {
    // 检查 Python 后端连接
    checkPythonConnection()
  }, [])

  const checkPythonConnection = async () => {
    try {
      if (window.electronAPI) {
        const result = await window.electronAPI.testPythonConnection()
        setPythonStatus(result.status === 'ok' ? 'connected' : 'error')
      } else {
        setPythonStatus('development')
      }
    } catch (error) {
      setPythonStatus('error')
    }
  }

  const handleComparisonComplete = (taskId, result) => {
    setCurrentTaskId(taskId)
    setCurrentResult(result)
    
    // 添加到历史记录
    const newTask = {
      id: taskId,
      timestamp: new Date().toISOString(),
      result: result
    }
    setTaskHistory(prev => [newTask, ...prev])
    
    // 自动切换到结果页
    setActiveTab('results')
  }

  const renderContent = () => {
    switch (activeTab) {
      case 'connections':
        return <ConnectionManager />
      case 'comparison':
        return <ComparisonTask onComplete={handleComparisonComplete} />
      case 'results':
        return <ResultDisplay taskId={currentTaskId} resultData={currentResult} />
      default:
        return <ConnectionManager />
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>数据库比对工具</h1>
        <div className={`status-indicator ${pythonStatus}`}>
          Python 后端: {pythonStatus === 'connected' ? '已连接' : 
                       pythonStatus === 'checking' ? '检查中...' :
                       pythonStatus === 'development' ? '开发模式' : '未连接'}
        </div>
      </header>
      
      <nav className="app-nav">
        <button 
          className={activeTab === 'connections' ? 'active' : ''}
          onClick={() => setActiveTab('connections')}
        >
          连接管理
        </button>
        <button 
          className={activeTab === 'comparison' ? 'active' : ''}
          onClick={() => setActiveTab('comparison')}
        >
          新建比对
        </button>
        <button 
          className={activeTab === 'results' ? 'active' : ''}
          onClick={() => setActiveTab('results')}
        >
          比对结果
        </button>
      </nav>
      
      <main className="app-main">
        {renderContent()}
      </main>
    </div>
  )
}

export default App
