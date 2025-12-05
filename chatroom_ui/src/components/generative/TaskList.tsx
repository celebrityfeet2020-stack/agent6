import React from 'react';
import { CheckCircle, Circle, XCircle } from 'lucide-react';

interface Task {
  id: string;
  title: string;
  status: 'pending' | 'completed' | 'failed';
  description?: string;
}

interface TaskListProps {
  tasks: Task[];
  title?: string;
}

const TaskList: React.FC<TaskListProps> = ({ tasks, title }) => {
  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-400" />;
    }
  };
  
  return (
    <div className="task-list-card">
      {title && <h3 className="task-list-title">{title}</h3>}
      
      <div className="task-list">
        {tasks.map((task) => (
          <div key={task.id} className="task-item">
            <div className="task-icon">{getStatusIcon(task.status)}</div>
            <div className="task-content">
              <p className="task-title">{task.title}</p>
              {task.description && <p className="task-description">{task.description}</p>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskList;
