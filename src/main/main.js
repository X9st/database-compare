const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

// 配置文件路径
const userDataPath = app.getPath('userData');
const connectionsFilePath = path.join(userDataPath, 'connections.json');
const tasksFilePath = path.join(userDataPath, 'tasks.json');

// 确保配置文件存在
if (!fs.existsSync(connectionsFilePath)) {
  fs.writeFileSync(connectionsFilePath, JSON.stringify([]));
}
if (!fs.existsSync(tasksFilePath)) {
  fs.writeFileSync(tasksFilePath, JSON.stringify({}));
}

let mainWindow;
let pythonProcess = null;

// 启动 Python 后端服务
function startPythonService() {
  const pythonPath = path.join(__dirname, '../../src/python-service/python/bin/python');
  const scriptPath = path.join(__dirname, '../../src/python-service/src/app.py');
  
  // 检查是否使用打包后的 Python 可执行文件
  const isPackaged = app.isPackaged;
  let pythonExecutable;
  
  if (isPackaged) {
    // 生产环境：使用打包的 Python 可执行文件
    pythonExecutable = path.join(process.resourcesPath, 'python-service/python');
  } else {
    // 开发环境：使用系统 Python 或便携版 Python
    pythonExecutable = process.env.PYTHON_PATH || 'python3';
  }
  
  pythonProcess = spawn(pythonExecutable, [scriptPath], {
    cwd: path.join(__dirname, '../../src/python-service'),
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Python: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Python Error: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Python process exited with code ${code}`);
  });
}

// 创建主窗口
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    }
  });

  // 开发环境加载 Vite 开发服务器
  if (process.env.NODE_ENV === 'development') {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    // 生产环境加载打包后的文件
    mainWindow.loadFile(path.join(__dirname, '../renderer/dist/index.html'));
  }
}

// IPC 通信：测试 Python 后端连接
ipcMain.handle('test-python-connection', async () => {
  try {
    const response = await fetch('http://localhost:5000/api/health');
    return await response.json();
  } catch (error) {
    return { status: 'error', message: error.message };
  }
});

// IPC 通信：测试数据库连接
ipcMain.handle('test-database-connection', async (event, config) => {
  try {
    const response = await fetch('http://localhost:5000/api/databases/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return await response.json();
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：获取数据库表列表
ipcMain.handle('get-database-tables', async (event, config) => {
  try {
    const response = await fetch('http://localhost:5000/api/databases/tables', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    return await response.json();
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：保存连接配置
ipcMain.handle('save-connection', async (event, connection) => {
  try {
    const connections = JSON.parse(fs.readFileSync(connectionsFilePath, 'utf8'));
    
    if (connection.id) {
      // 更新现有连接
      const index = connections.findIndex(c => c.id === connection.id);
      if (index !== -1) {
        connections[index] = connection;
      } else {
        connections.push(connection);
      }
    } else {
      // 新建连接
      connection.id = Date.now().toString();
      connections.push(connection);
    }
    
    fs.writeFileSync(connectionsFilePath, JSON.stringify(connections, null, 2));
    return { success: true, connection };
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：获取所有连接
ipcMain.handle('get-connections', async () => {
  try {
    const connections = JSON.parse(fs.readFileSync(connectionsFilePath, 'utf8'));
    // 脱敏处理
    const sanitizedConnections = connections.map(c => ({
      ...c,
      password: c.password ? '********' : ''
    }));
    return { success: true, connections: sanitizedConnections };
  } catch (error) {
    return { success: false, message: error.message, connections: [] };
  }
});

// IPC 通信：删除连接
ipcMain.handle('delete-connection', async (event, id) => {
  try {
    const connections = JSON.parse(fs.readFileSync(connectionsFilePath, 'utf8'));
    const filtered = connections.filter(c => c.id !== id);
    fs.writeFileSync(connectionsFilePath, JSON.stringify(filtered, null, 2));
    return { success: true };
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：获取完整连接信息（包含密码）
ipcMain.handle('get-connection-full', async (event, id) => {
  try {
    const connections = JSON.parse(fs.readFileSync(connectionsFilePath, 'utf8'));
    const connection = connections.find(c => c.id === id);
    return { success: true, connection };
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：启动比对任务
ipcMain.handle('start-comparison', async (event, taskConfig) => {
  try {
    const response = await fetch('http://localhost:5000/api/comparison/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(taskConfig)
    });
    const result = await response.json();
    
    if (result.success) {
      // 保存任务配置
      const tasks = JSON.parse(fs.readFileSync(tasksFilePath, 'utf8'));
      tasks[result.task_id] = {
        ...taskConfig,
        task_id: result.task_id,
        status: 'running',
        created_at: new Date().toISOString()
      };
      fs.writeFileSync(tasksFilePath, JSON.stringify(tasks, null, 2));
    }
    
    return result;
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：获取比对进度
ipcMain.handle('get-comparison-progress', async (event, taskId) => {
  try {
    const response = await fetch(`http://localhost:5000/api/comparison/${taskId}/progress`);
    return await response.json();
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：获取比对结果
ipcMain.handle('get-comparison-result', async (event, taskId) => {
  try {
    const response = await fetch(`http://localhost:5000/api/comparison/${taskId}/result`);
    const result = await response.json();
    
    if (result.success && result.result) {
      // 更新任务状态
      const tasks = JSON.parse(fs.readFileSync(tasksFilePath, 'utf8'));
      if (tasks[taskId]) {
        tasks[taskId].status = result.status;
        tasks[taskId].result = result.result;
        fs.writeFileSync(tasksFilePath, JSON.stringify(tasks, null, 2));
      }
    }
    
    return result;
  } catch (error) {
    return { success: false, message: error.message };
  }
});

// IPC 通信：导出报告
ipcMain.handle('export-report', async (event, taskId, format) => {
  try {
    const tasks = JSON.parse(fs.readFileSync(tasksFilePath, 'utf8'));
    const task = tasks[taskId];
    
    if (!task || !task.result) {
      return { success: false, message: '任务不存在或无结果' };
    }
    
    // TODO: 实现报告导出逻辑
    return { success: true, message: '报告导出功能开发中' };
  } catch (error) {
    return { success: false, message: error.message };
  }
});

app.whenReady().then(() => {
  startPythonService();
  
  // 等待 Python 服务启动
  setTimeout(() => {
    createWindow();
  }, 2000);

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
});
