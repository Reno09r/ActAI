"use client"

import type React from "react"
import { useState, useEffect, useRef } from "react"
import {
  ChevronRight,
  ChevronDown,
  FileText,
  Settings,
  Calendar,
  Clock,
  Target,
  Trophy,
  ArrowLeft,
  Check,
  Edit3,
  Save,
  Plus,
  BookOpen,
  AlertTriangle, // For error display
  Loader2, // For loading state
  PlayCircle, // Для in progress
  Clock as ClockIcon, // Для pending
  LogOut,
} from "lucide-react"
import CreateProjectModal from "./CreateProjectModal"
import { useAuth } from '../contexts/AuthContext'
import { useNavigate } from 'react-router-dom'
import TaskAdaptationModal from './TaskAdaptationModal'
import VoiceRecordButton from './VoiceRecordButton'
import { useToast } from '../contexts/ToastContext'
import DotsAnimation from './DotsAnimation'

// Добавляем тип для статусов задач
type TaskStatus = "pending" | "in_progress" | "completed";

// --- INTERFACES (Adjusted to better match backend and handle nulls) ---
interface Task {
  id: number
  title: string
  description: string | null // Can be null
  due_date: string // Assuming backend sends as string
  priority: string // "high", "medium", "low"
  estimated_hours: number | null // Can be null
  status: TaskStatus // e.g., "pending", "in_progress", "completed"
  ai_suggestion: string | null // Can be null
  // Add any other fields from backend TaskResponse
}

interface Milestone {
  id: number
  title: string
  description: string | null // Can be null
  order: number
  tasks: Task[]
  // Add any other fields from backend MilestoneResponse
  // e.g. plan_id?: number; status?: string; start_date?: string; end_date?: string;
}

interface Project {
  id: number
  title: string
  description: string | null
  estimated_duration_weeks: number | null
  weekly_commitment_hours: string | null
  difficulty_level: string | null
  prerequisites: string | null // New field from PlanResponse
  user_id: number // New field from PlanResponse
  status: string // New field from PlanResponse (e.g. "active", "completed")
  start_date: string
  end_date: string
  progress_percentage: number
  tags: string | null // New field from PlanResponse
  milestones: Milestone[]
  created_at: string // New field from PlanResponse
  updated_at: string // New field from PlanResponse
}

interface Notes {
  [key: string]: string
}

interface CompletedTasks {
  [key: number]: boolean
}

interface CompletedMilestones {
  [key: number]: boolean
}

// Placeholder for your API token - in a real app, get this from auth context/storage
const API_BASE_URL = "/api" // Assuming proxy or Next.js API route

// Добавляем новый интерфейс для задач по срокам
interface TasksByDate {
  today: Task[];
  tomorrow: Task[];
  upcoming: Task[];
}

const Dashboard: React.FC = () => {
  const { token, logout } = useAuth();
  const { showToast } = useToast();
  const [projects, setProjects] = useState<Project[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)

  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [expandedMilestone, setExpandedMilestone] = useState<number | null>(null)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [selectedMilestone, setSelectedMilestone] = useState<Milestone | null>(null)
  const [view, setView] = useState<"projects" | "milestones" | "milestone" | "task">("projects")
  const [completedTasks, setCompletedTasks] = useState<CompletedTasks>({})
  const [completedMilestones, setCompletedMilestones] = useState<CompletedMilestones>({})
  const [notes, setNotes] = useState<Notes>(() => {
    // Загружаем заметки из localStorage при инициализации
    const savedNotes = localStorage.getItem('projectNotes')
    return savedNotes ? JSON.parse(savedNotes) : {}
  })
  const [editingNote, setEditingNote] = useState<string | null>(null)
  const [updatingTaskId, setUpdatingTaskId] = useState<number | null>(null)
  const [updateError, setUpdateError] = useState<string | null>(null)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [editingMilestone, setEditingMilestone] = useState<Milestone | null>(null)
  const [isSaving, setIsSaving] = useState(false)
  const [tasksByDate, setTasksByDate] = useState<TasksByDate>({
    today: [],
    tomorrow: [],
    upcoming: []
  });
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [inProgressTasks, setInProgressTasks] = useState<Task[]>([]);
  const [isLoadingInProgress, setIsLoadingInProgress] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [isAdaptationModalOpen, setIsAdaptationModalOpen] = useState(false);
  const [adaptingTaskId, setAdaptingTaskId] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const navigate = useNavigate();
  const [sidebarWidth, setSidebarWidth] = useState(320); // Начальная ширина сайдбара
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  // Добавляем обработчики для изменения размера
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      
      const newWidth = e.clientX;
      if (newWidth >= 240 && newWidth <= 480) { // Минимальная и максимальная ширина
        setSidebarWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  const handleCreateSuccess = () => {
    // Перезагружаем список проектов после успешного создания
    fetchProjects();
  };

  const fetchProjects = async () => {
    setIsLoading(true)
    setError(null)
    try {
      const response = await fetch(`${API_BASE_URL}/plans/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })
      if (!response.ok) {
        throw new Error(`Failed to fetch projects: ${response.statusText} (Status: ${response.status})`)
      }
      const data: Project[] = await response.json()
      setProjects(data)

      // Инициализируем completedTasks и completedMilestones на основе статусов
      const initialCompletedTasks: CompletedTasks = {};
      const initialCompletedMilestones: CompletedMilestones = {};

      data.forEach(project => {
        project.milestones.forEach(milestone => {
          // Ensure all tasks in the milestone are completed AND the milestone is not empty
          const allTasksInMilestoneCompleted = 
            milestone.tasks.length > 0 && // Important: an empty milestone isn't "completed" by doing work
            milestone.tasks.every(task => task.status === "completed");
          
          initialCompletedMilestones[milestone.id] = allTasksInMilestoneCompleted; // Explicitly true or false

          milestone.tasks.forEach(task => {
            initialCompletedTasks[task.id] = task.status === "completed"; // Explicitly true or false
          });
        });
      });

      setCompletedTasks(initialCompletedTasks);
      setCompletedMilestones(initialCompletedMilestones);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message)
      } else {
        setError("An unknown error occurred")
      }
      console.error("Error fetching projects:", err)
    } finally {
      setIsLoading(false)
    }
  }
  const getTaskStatus = (task: Task): TaskStatus => {
    // Проверяем актуальный статус из объекта задачи
    if (task.status) {
      return task.status as TaskStatus;
    }
    
    // Fallback на локальные состояния
    if (completedTasks[task.id]) {
      return "completed";
    }
    
    if (inProgressTasks.some(t => t.id === task.id)) {
      return "in_progress";
    }
    
    return "pending";
  };
  
  // Обновляем функцию fetchTasksByDate
  const fetchTasksByDate = async () => {
    setIsLoadingTasks(true);
    try {
      const [todayResponse, tomorrowResponse, upcomingResponse] = await Promise.all([
        fetch(`${API_BASE_URL}/tasks/today`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch(`${API_BASE_URL}/tasks/tomorrow`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }),
        fetch(`${API_BASE_URL}/tasks/upcoming`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        })
      ]);

      const [todayTasks, tomorrowTasks, upcomingTasks] = await Promise.all([
        todayResponse.json(),
        tomorrowResponse.json(),
        upcomingResponse.json()
      ]);

      // Обновляем состояния completedTasks и inProgressTasks
      const newCompletedTasks = { ...completedTasks };
      const newInProgressTasks = [...inProgressTasks];

      [...todayTasks, ...tomorrowTasks, ...upcomingTasks].forEach(task => {
        if (task.status === "completed") {
          newCompletedTasks[task.id] = true;
        } else if (task.status === "in_progress") {
          newInProgressTasks.push(task);
          newCompletedTasks[task.id] = false;
        } else { // 'pending' и другие
          newCompletedTasks[task.id]  = false; // Явно не завершена
        }
      });

      setCompletedTasks(newCompletedTasks);
      setInProgressTasks(newInProgressTasks);

      setTasksByDate({
        today: todayTasks,
        tomorrow: tomorrowTasks,
        upcoming: upcomingTasks
      });
    } catch (err) {
      console.error('Error fetching tasks by date:', err);
    } finally {
      setIsLoadingTasks(false);
    }
  };

  // Добавляем функцию для загрузки задач in progress
  const fetchInProgressTasks = async () => {
    setIsLoadingInProgress(true);
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/in-progress`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error('Failed to fetch in-progress tasks');
      }
      const tasks = await response.json();
      setInProgressTasks(tasks);
      
      // Синхронизируем локальные состояния с реальными данными
      const newCompletedTasks: { [key: number]: boolean } = {};
      
      // Помечаем все in-progress задачи
      tasks.forEach((task: Task) => {
        newCompletedTasks[task.id] = false;
      });
      
      setCompletedTasks(prev => ({
        ...prev,
        ...newCompletedTasks
      }));
    } catch (err) {
      console.error('Error fetching in-progress tasks:', err);
    } finally {
      setIsLoadingInProgress(false);
    }
  };

  useEffect(() => {
    fetchProjects();
    fetchTasksByDate();
    fetchInProgressTasks();
  }, []);

  const selectProject = (project: Project) => {
    setSelectedProject(project)
    setView("milestones")
    setExpandedMilestone(project.milestones[0]?.id || null)
  }

  const toggleMilestone = (milestoneId: number) => {
    setExpandedMilestone((prev) => (prev === milestoneId ? null : milestoneId))
  }

  const openMilestone = (milestone: Milestone) => {
    setSelectedMilestone(milestone)
    setSelectedTask(null) // Clear selected task when opening a milestone
    setView("milestone")
  }

  const openTask = (task: Task) => {
    setSelectedTask(task)
    // Keep selectedMilestone if navigating from a milestone view,
    // or find parent milestone if navigating from somewhere else (not currently implemented)
    // For now, we assume openTask is called from a context where selectedMilestone is relevant or needs to be cleared.
    // If task is opened from sidebar, selectedMilestone should be its parent.
    // This part might need refinement based on exact navigation flows.
    // For simplicity, if opening task from sidebar, we might need to find its parent milestone.
    // For now, let's ensure selectedMilestone is cleared if task is opened independently.
    // However, the current flow opens tasks from within a milestone's context.
    // The `goBack` logic correctly handles setting selectedMilestone back.
    setView("task")
  }

  const goBack = () => {
    if (view === "task") {
      // If we came from a specific milestone view, go back to it
      // This assumes selectedTask always belongs to the selectedMilestone if it's set
      // Find the milestone this task belongs to if selectedMilestone is not set
      if (!selectedMilestone && selectedTask && selectedProject) {
         const parentMilestone = selectedProject.milestones.find(m => m.tasks.some(t => t.id === selectedTask.id));
         setSelectedMilestone(parentMilestone || null);
      }
      setView("milestone")
      setSelectedTask(null) // Clear selected task
    } else if (view === "milestone") {
      setView("milestones")
      setSelectedMilestone(null) // Clear selected milestone
    } else if (view === "milestones") {
      setView("projects")
      setSelectedProject(null) // Clear selected project
      setExpandedMilestone(null) // Clear expanded milestone
    }
  }

  // Обновляем функцию calculateProjectProgress
  const calculateProjectProgress = (project: Project): number => {
    let totalTasks = 0;
    let completedTasksCount = 0;
  
    project.milestones.forEach(milestone => {
      milestone.tasks.forEach(task => {
        totalTasks++;
        if (task.status === "completed") {
          completedTasksCount++;
        }
      });
    });
  
    if (totalTasks === 0) return 0;
    
    const progress = (completedTasksCount / totalTasks) * 100;
    
    // Умное округление
    const rounded = Math.round(progress);
    if (Math.abs(progress - rounded) < 0.1) {
      return rounded;
    }
    
    return Math.round(progress * 10) / 10;
  };

  // Добавляем функцию для поиска проекта по ID задачи
  const findProjectByTaskId = (taskId: number): Project | undefined => {
    return projects.find(project => 
      project.milestones.some(milestone => 
        milestone.tasks.some(task => task.id === taskId)
      )
    );
  };

  // Обновляем функцию toggleTaskStatus
  const toggleTaskStatus = async (taskId: number, newStatus: TaskStatus) => {
    try {
      setUpdatingTaskId(taskId);
      setUpdateError(null);
      
      const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/status?status=${newStatus}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });
  
      if (!response.ok) {
        throw new Error(`Failed to update task status: ${response.statusText}`);
      }
  
      // Немедленно обновляем локальные состояния
      updateLocalTaskStates(taskId, newStatus);
      
      // Обновляем задачи во всех представлениях
      updateTaskInAllViews(taskId, newStatus);
      
      // Обновляем проект и milestone
      updateProjectAndMilestone(taskId, newStatus);
  
    } catch (err) {
      setUpdateError(err instanceof Error ? err.message : 'Failed to update task status');
      console.error('Error updating task status:', err);
    } finally {
      setUpdatingTaskId(null);
    }
  };
  
  // Вспомогательная функция для обновления локальных состояний
  const updateLocalTaskStates = (taskId: number, newStatus: TaskStatus) => {
    if (newStatus === "in_progress") {
      setInProgressTasks(prev => {
        const exists = prev.some(task => task.id === taskId);
        if (!exists) {
          const task = findTaskById(taskId);
          if (task) {
            return [...prev, task];
          }
        }
        return prev;
      });
      setCompletedTasks(prev => ({ ...prev, [taskId]: false }));
    } else if (newStatus === "completed") {
      setInProgressTasks(prev => prev.filter(task => task.id !== taskId));
      setCompletedTasks(prev => ({ ...prev, [taskId]: true }));
    } else { // pending
      setInProgressTasks(prev => prev.filter(task => task.id !== taskId));
      setCompletedTasks(prev => ({ ...prev, [taskId]: false }));
    }
  };
  
  // Вспомогательная функция для обновления задач во всех представлениях
  const updateTaskInAllViews = (taskId: number, newStatus: TaskStatus) => {
    // Обновляем задачи в tasksByDate
    setTasksByDate(prev => ({
      today: prev.today.map(task => 
        task.id === taskId ? { ...task, status: newStatus } : task
      ),
      tomorrow: prev.tomorrow.map(task => 
        task.id === taskId ? { ...task, status: newStatus } : task
      ),
      upcoming: prev.upcoming.map(task => 
        task.id === taskId ? { ...task, status: newStatus } : task
      )
    }));
  
    // Обновляем выбранную задачу, если она изменилась
    if (selectedTask?.id === taskId) {
      setSelectedTask(prev => prev ? { ...prev, status: newStatus } : null);
    }
  };
  
  // Вспомогательная функция для обновления проекта и milestone
  const updateProjectAndMilestone = (taskId: number, newStatus: TaskStatus) => {
    const project = findProjectByTaskId(taskId);
    if (!project) return;

    // Обновляем проект и milestone
    const updatedProject = {
      ...project,
      milestones: project.milestones.map(milestone => {
        const updatedTasks = milestone.tasks.map(task =>
          task.id === taskId ? { ...task, status: newStatus } : task
        );

        const updatedMilestone = {
          ...milestone,
          tasks: updatedTasks
        };

        // Обновляем статус milestone
        // Check if ALL tasks in this specific milestone are now completed
        const allTasksInThisMilestoneCompleted =
          updatedTasks.length > 0 && // Ensure milestone is not empty
          updatedTasks.every(task => task.status === "completed");

        setCompletedMilestones(prev => ({
          ...prev,
          [milestone.id]: allTasksInThisMilestoneCompleted
        }));

        return updatedMilestone;
      })
    };

    // Обновляем прогресс проекта
    const newProgress = calculateProjectProgress(updatedProject);
    updatedProject.progress_percentage = newProgress;

    // Обновляем состояние проекта
    if (selectedProject?.id === project.id) {
      setSelectedProject(updatedProject);

      // --- !! KEY CHANGE IS HERE !! ---
      // If the currently viewed milestone (selectedMilestone) belongs to the updated project,
      // we need to update selectedMilestone state as well, so it re-renders with the fresh task data.
      if (selectedMilestone) {
        // Find the updated version of the selected milestone from the updated project data
        const refreshedSelectedMilestone = updatedProject.milestones.find(m => m.id === selectedMilestone.id);
        if (refreshedSelectedMilestone) {
          setSelectedMilestone(refreshedSelectedMilestone); // Update selectedMilestone state
        }
      }
      // --- !! END OF KEY CHANGE !! ---
    }

    // Обновляем проект в списке проектов
    setProjects(prev => prev.map(p =>
      p.id === project.id ? updatedProject : p
    ));
  };
  // Обновляем компонент TasksByDateSection
  const TasksByDateSection = () => {
    if (isLoadingTasks) {
      return (
        <div className="flex items-center justify-center p-4">
          <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
        </div>
      );
    }
  
    const handleTaskClick = (task: Task, event: React.MouseEvent) => {
      // Если клик был по иконке статуса, не переходим к деталям
      if ((event.target as HTMLElement).closest('.task-status-button')) {
        return;
      }
  
      // Находим проект и milestone для этой задачи
      const project = projects.find(p => 
        p.milestones.some(m => m.tasks.some(t => t.id === task.id))
      );
      
      if (project) {
        const milestone = project.milestones.find(m => 
          m.tasks.some(t => t.id === task.id)
        );
        
        if (milestone) {
          setSelectedProject(project);
          setSelectedMilestone(milestone);
          setSelectedTask(task);
          setView("task");
        }
      }
    };
  
    const renderTaskList = (tasks: Task[], title: string, color: string) => (
      <div className="bg-white rounded-lg shadow p-4 mb-4">
        <h3 className={`text-lg font-semibold mb-3 ${color}`}>{title}</h3>
        {tasks.length === 0 ? (
          <p className="text-gray-500 text-sm">No tasks</p>
        ) : (
          <div className="space-y-2">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="flex items-center p-2 hover:bg-gray-50 rounded cursor-pointer"
                onClick={(e) => handleTaskClick(task, e)}
              >
                <div className="task-status-button">
                  <TaskStatusButton task={task} />
                </div>
                <div className="ml-2 flex-1">
                  <p className={`text-sm ${
                    task.status === 'completed'
                      ? 'line-through text-gray-400' 
                      : task.status === 'in_progress'
                        ? 'text-blue-600'
                        : 'text-gray-700'
                  }`}>
                    {task.title}
                  </p>
                  <div className="flex items-center text-xs text-gray-500 mt-1">
                    <span className="mr-2">Due: {formatDate(task.due_date)}</span>
                    <span className={`px-2 py-0.5 rounded-full ${
                      task.priority === "high"
                        ? "bg-red-100 text-red-700"
                        : task.priority === "medium"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-green-100 text-green-700"
                    }`}>
                      {task.priority}
                    </span>
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                      task.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : task.status === 'in_progress'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-gray-100 text-gray-700'
                    }`}>
                      {formatTaskStatus(task.status)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {renderTaskList(tasksByDate.today, "Today's Tasks", "text-blue-600")}
        {renderTaskList(tasksByDate.tomorrow, "Tomorrow's Tasks", "text-purple-600")}
        {renderTaskList(tasksByDate.upcoming, "Upcoming Tasks", "text-green-600")}
      </div>
    );
  };

  // Добавляем функцию форматирования статуса
  const formatTaskStatus = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'in_progress':
        return 'In Progress';
      case 'pending':
        return 'Pending';
      case 'completed':
        return 'Completed';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  // Обновляем компонент TaskStatusButton
  const TaskStatusButton = ({ task }: { task: Task }) => {
    const currentStatus = getTaskStatus(task);
  
    const getStatusIcon = () => {
      switch (currentStatus) {
        case 'completed':
          return <Check className="w-4 h-4" />;
        case 'in_progress':
          return <PlayCircle className="w-4 h-4" />;
        case 'pending':
        default:
          return <ClockIcon className="w-4 h-4" />;
      }
    };
  
    const getStatusColor = () => {
      switch (currentStatus) {
        case 'completed':
          return "bg-green-100 text-green-700 hover:bg-green-200";
        case 'in_progress':
          return "bg-blue-100 text-blue-700 hover:bg-blue-200";
        case 'pending':
        default:
          return "bg-gray-100 text-gray-700 hover:bg-gray-200";
      }
    };
  
    const getStatusText = () => {
      switch (currentStatus) {
        case 'completed':
          return "Completed";
        case 'in_progress':
          return "In Progress";
        case 'pending':
        default:
          return "Pending";
      }
    };
  
    const getNextStatus = () => {
      switch (currentStatus) {
        case 'pending':
          return 'Start';
        case 'in_progress':
          return 'Complete';
        case 'completed':
          return 'Reset';
        default:
          return 'Start';
      }
    };
  
    return (
      <button
        onClick={(e) => {
          e.stopPropagation(); // Предотвращаем всплытие события
          toggleTaskCompletion(task.id);
        }}
        className={`p-2 rounded-full ${getStatusColor()} transition-all duration-200 flex items-center gap-1 text-xs font-medium`}
        disabled={updatingTaskId === task.id}
        title={`Click to ${getNextStatus().toLowerCase()}`}
      >
        {updatingTaskId === task.id ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <>
            {getStatusIcon()}
            <span>{getStatusText()}</span>
          </>
        )}
      </button>
    );
  };
  
  

  // Восстанавливаем функцию formatDate
  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return "N/A"
    try {
      return new Date(dateString).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    } catch (e) {
      return "Invalid Date"
    }
  }

  // Восстанавливаем компонент CustomCheckbox
  const CustomCheckbox = ({
    checked,
    onChange,
    size = "md",
    taskId,
  }: { 
    checked: boolean; 
    onChange: (event: React.MouseEvent<HTMLButtonElement>) => void; 
    size?: "sm" | "md";
    taskId?: number;
  }) => {
    const sizeClasses = size === "sm" ? "w-4 h-4" : "w-5 h-5"
    const isLoading = taskId !== undefined && updatingTaskId === taskId

    return (
      <button
        onClick={(e) => {
          e.stopPropagation()
          onChange(e)
        }}
        disabled={isLoading}
        className={`${sizeClasses} rounded border-2 flex items-center justify-center transition-all duration-200 ${
          checked ? "bg-green-500 border-green-500 text-white" : "border-gray-300 hover:border-green-400"
        } ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
      >
        {isLoading ? (
          <Loader2 className="w-3 h-3 animate-spin" />
        ) : checked ? (
          <Check className="w-3 h-3" />
        ) : null}
      </button>
    )
  }

  // Восстанавливаем компонент NotesSection
  const NotesSection = ({ noteKey, placeholder }: { noteKey: string; placeholder: string }) => {
    const [isEditing, setIsEditing] = useState(false)
    const noteText = notes[noteKey] || ""
    const textareaRef = useRef<HTMLTextAreaElement>(null)

    useEffect(() => {
      if (isEditing && textareaRef.current) {
        textareaRef.current.focus()
      }
    }, [isEditing])

    const handleSave = () => {
      if (textareaRef.current) {
        updateNote(noteKey, textareaRef.current.value)
      }
      setIsEditing(false)
    }

    return (
      <div className="mt-4 bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-700">My Notes</h4>
          <button
            onClick={() => isEditing ? handleSave() : setIsEditing(true)}
            className="text-gray-500 hover:text-gray-700 transition-colors p-1"
          >
            {isEditing ? <Save className="w-4 h-4" /> : <Edit3 className="w-4 h-4" />}
          </button>
        </div>
        {isEditing ? (
          <textarea
            ref={textareaRef}
            defaultValue={noteText}
            placeholder={placeholder}
            className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={4}
            onBlur={handleSave}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.metaKey) {
                handleSave()
              }
            }}
          />
        ) : (
          <div 
            className="text-gray-600 text-sm min-h-[60px] p-3 bg-white rounded border whitespace-pre-wrap cursor-pointer hover:bg-gray-50"
            onClick={() => setIsEditing(true)}
          >
            {noteText || <span className="text-gray-400 italic">{placeholder}</span>}
          </div>
        )}
      </div>
    )
  }

  // Обновляем функцию toggleMilestoneCompletion
  const toggleMilestoneCompletion = async (milestoneId: number) => {
    if (!selectedProject) return;

    try {
      const isCurrentlyCompleted = completedMilestones[milestoneId];
      const newStatus = !isCurrentlyCompleted;
      const newTaskStatus: TaskStatus = newStatus ? "completed" : "pending";

      // Обновляем статус milestone
      setCompletedMilestones(prev => ({
        ...prev,
        [milestoneId]: newStatus
      }));

      // Обновляем статусы всех задач в milestone
      const milestone = selectedProject.milestones.find(m => m.id === milestoneId);
      if (milestone) {
        // Обновляем статусы задач
        for (const task of milestone.tasks) {
          if (newStatus) {
            setInProgressTasks(prev => prev.filter(t => t.id !== task.id));
            setCompletedTasks(prev => ({ ...prev, [task.id]: true }));
          } else {
            setInProgressTasks(prev => prev.filter(t => t.id !== task.id));
            setCompletedTasks(prev => ({ ...prev, [task.id]: false }));
          }

          // Обновляем задачи в tasksByDate
          setTasksByDate(prev => ({
            today: prev.today.map(t => 
              t.id === task.id ? { ...t, status: newTaskStatus } : t
            ),
            tomorrow: prev.tomorrow.map(t => 
              t.id === task.id ? { ...t, status: newTaskStatus } : t
            ),
            upcoming: prev.upcoming.map(t => 
              t.id === task.id ? { ...t, status: newTaskStatus } : t
            )
          }));

          // Обновляем статус задачи на сервере
          await fetch(`${API_BASE_URL}/tasks/${task.id}/status?status=${newTaskStatus}`, {
            method: 'PATCH',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });
        }
      }

      // Обновляем проект
      const updatedProject = {
        ...selectedProject,
        milestones: selectedProject.milestones.map(milestone => {
          if (milestone.id === milestoneId) {
            return {
              ...milestone,
              tasks: milestone.tasks.map(task => ({
                ...task,
                status: newTaskStatus
              }))
            };
          }
          return milestone;
        })
      };

      // Обновляем прогресс проекта
      const newProgress = calculateProjectProgress(updatedProject);
      updatedProject.progress_percentage = newProgress;

      // Обновляем состояние проекта
      setSelectedProject(updatedProject);

      // Обновляем проект в списке проектов
      setProjects(prev => prev.map(p => 
        p.id === selectedProject.id ? updatedProject : p
      ));

    } catch (err) {
      console.error('Error updating milestone status:', err);
      // Восстанавливаем предыдущее состояние в случае ошибки
      setCompletedMilestones(prev => ({
        ...prev,
        [milestoneId]: !prev[milestoneId]
      }));
    }
  };

  // Восстанавливаем функцию updateNote
  const updateNote = (key: string, note: string) => {
    const newNotes = {
      ...notes,
      [key]: note,
    }
    setNotes(newNotes)
    // Сохраняем в localStorage
    localStorage.setItem('projectNotes', JSON.stringify(newNotes))
  }

  // Восстанавливаем функцию updateTask
  const updateTask = async (taskId: number, updates: Partial<Task>) => {
    try {
      setIsSaving(true)
      setUpdateError(null)

      // Удаляем undefined значения
      const cleanUpdates = Object.fromEntries(
        Object.entries(updates).filter(([_, value]) => value !== undefined)
      )

      const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanUpdates),
      })

      if (!response.ok) {
        throw new Error(`Failed to update task: ${response.statusText}`)
      }

      const updatedTask = await response.json()
      
      // Обновляем задачу в локальном состоянии
      if (selectedProject) {
        const updatedProject = {
          ...selectedProject,
          milestones: selectedProject.milestones.map(milestone => ({
            ...milestone,
            tasks: milestone.tasks.map(task => 
              task.id === taskId ? { ...task, ...updatedTask } : task
            )
          }))
        }
        
        // Обновляем выбранный проект
        setSelectedProject(updatedProject)
        
        // Обновляем проект в списке проектов
        setProjects(prev => prev.map(project => 
          project.id === selectedProject.id ? updatedProject : project
        ))

        // Если мы находимся в режиме просмотра задачи, обновляем выбранную задачу
        if (selectedTask?.id === taskId) {
          setSelectedTask(updatedTask)
        }
      }

      setEditingTask(null)
    } catch (err) {
      setUpdateError(err instanceof Error ? err.message : 'Failed to update task')
      console.error('Error updating task:', err)
    } finally {
      setIsSaving(false)
    }
  }

  // Восстанавливаем функцию updateMilestone
  const updateMilestone = async (milestoneId: number, updates: Partial<Milestone>) => {
    try {
      setIsSaving(true)
      setUpdateError(null)

      // Удаляем undefined значения
      const cleanUpdates = Object.fromEntries(
        Object.entries(updates).filter(([_, value]) => value !== undefined)
      )

      const response = await fetch(`${API_BASE_URL}/milestones/${milestoneId}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanUpdates),
      })

      if (!response.ok) {
        throw new Error(`Failed to update milestone: ${response.statusText}`)
      }

      const updatedMilestone = await response.json()
      
      // Обновляем этап в локальном состоянии
      if (selectedProject) {
        const updatedProject = {
          ...selectedProject,
          milestones: selectedProject.milestones.map(milestone => 
            milestone.id === milestoneId ? { ...milestone, ...updatedMilestone } : milestone
          )
        }
        
        // Обновляем выбранный проект
        setSelectedProject(updatedProject)
        
        // Обновляем проект в списке проектов
        setProjects(prev => prev.map(project => 
          project.id === selectedProject.id ? updatedProject : project
        ))

        // Если мы находимся в режиме просмотра этапа, обновляем выбранный этап
        if (selectedMilestone?.id === milestoneId) {
          setSelectedMilestone(updatedMilestone)
        }
      }

      setEditingMilestone(null)
    } catch (err) {
      setUpdateError(err instanceof Error ? err.message : 'Failed to update milestone')
      console.error('Error updating milestone:', err)
    } finally {
      setIsSaving(false)
    }
  }
  const findTaskById = (taskId: number): Task | undefined => {
    for (const project of projects) {
      for (const milestone of project.milestones) {
        const task = milestone.tasks.find(t => t.id === taskId);
        if (task) return task;
      }
    }
    return undefined;
  };
  // Восстанавливаем функцию toggleTaskCompletion
  const toggleTaskCompletion = async (taskId: number) => {
    const task = findTaskById(taskId);
    if (!task) return;
    
    const currentStatus = getTaskStatus(task);
    let newStatus: TaskStatus;
    
    // Циклическое переключение: pending -> in_progress -> completed -> pending
    switch (currentStatus) {
      case "pending":
        newStatus = "in_progress";
        break;
      case "in_progress":
        newStatus = "completed";
        break;
      case "completed":
        newStatus = "pending";
        break;
      default:
        newStatus = "pending";
    }
    
    await toggleTaskStatus(taskId, newStatus);
  };
  

  // Добавляем функцию updateProject
  const updateProject = async (projectId: number, updates: Partial<Project>) => {
    try {
      setIsSaving(true)
      setUpdateError(null)

      const cleanUpdates = Object.fromEntries(
        Object.entries(updates).filter(([_, value]) => value !== undefined)
      )

      const response = await fetch(`${API_BASE_URL}/plans/${projectId}/`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(cleanUpdates),
      })

      if (!response.ok) {
        throw new Error(`Failed to update project: ${response.statusText}`)
      }

      const updatedProject = await response.json()
      
      // Обновляем проект в локальном состоянии
      setProjects(prev => prev.map(project => 
        project.id === projectId ? updatedProject : project
      ))

      // Если мы находимся в режиме просмотра проекта, обновляем выбранный проект
      if (selectedProject?.id === projectId) {
        setSelectedProject(updatedProject)
      }

      setEditingProject(null)
    } catch (err) {
      setUpdateError(err instanceof Error ? err.message : 'Failed to update project')
      console.error('Error updating project:', err)
    } finally {
      setIsSaving(false)
    }
  }

  // Функция для форматирования Prerequisites
  const formatPrerequisites = (prerequisites: string | null): string => {
    if (!prerequisites) return "N/A"
    // Удаляем квадратные скобки и кавычки
    return prerequisites.replace(/[\[\]"]/g, '')
  }

  const handleAdaptTask = async (taskId: number, message: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/tasks/${taskId}/adapt`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_message: message }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Ошибка при адаптации задачи');
      }

      const updatedTask = await response.json();

      // Обновляем все данные
      await Promise.all([
        fetchProjects(),
        fetchTasksByDate(),
        fetchInProgressTasks()
      ]);

    } catch (err) {
      throw new Error(err instanceof Error ? err.message : 'Ошибка при адаптации задачи');
    }
  };

  const openAdaptationModal = (taskId: number) => {
    setAdaptingTaskId(taskId);
    setIsAdaptationModalOpen(true);
  };

  const handleRecordingComplete = async (audioBlob: Blob) => {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.mp3');

      // Отправляем аудио на сервер для транскрибации
      const response = await fetch(`${API_BASE_URL}/audio/stt/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Ошибка при обработке аудио');
      }

      const data = await response.json();
      
      // Создаем новый проект на основе транскрибированного текста
      const projectResponse = await fetch(`${API_BASE_URL}/plans/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          objective: data.processed_text,
          duration: '4 weeks',
        }),
      });

      if (!projectResponse.ok) {
        throw new Error('Ошибка при создании проекта');
      }

      const project = await projectResponse.json();
      
      // Получаем озвучку информации о проекте
      const ttsResponse = await fetch(`${API_BASE_URL}/audio/tts/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text: `Project "${project.title}" created. ${project.description}`,
          gender: 'M',
        }),
      });

      if (!ttsResponse.ok) {
        throw new Error('Ошибка при генерации речи');
      }

      const ttsAudioBlob = await ttsResponse.blob();
      const audioUrl = URL.createObjectURL(ttsAudioBlob);
      const audio = new Audio(audioUrl);
      
      // Добавляем обработчики событий для аудио
      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => setIsPlaying(false);
      
      await audio.play();

      showToast('Project created!', 'success');
      fetchProjects(); // Обновляем список проектов
    } catch (error) {
      console.error('Error:', error);
      showToast('Произошла ошибка при создании проекта', 'error');
    } finally {
      // Сбрасываем состояние isProcessing в VoiceRecordButton
      const voiceRecordButton = document.querySelector('.voice-record-button') as HTMLElement;
      if (voiceRecordButton) {
        voiceRecordButton.dispatchEvent(new CustomEvent('recording-complete'));
      }
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center text-gray-600">
        <Loader2 className="h-8 w-8 animate-spin mr-2" />
        Loading projects...
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col h-screen items-center justify-center text-red-600 p-8">
        <AlertTriangle className="h-12 w-12 mb-4" />
        <h2 className="text-xl font-semibold mb-2">Error Loading Data</h2>
        <p className="text-center">{error}</p>
        <button
          onClick={() => window.location.reload()} // Simple reload, or re-fetch
          className="mt-4 px-4 py-2 bg-red-500 text-white rounded hover:bg-red-700"
        >
          Try Again
        </button>
      </div>
    )
  }

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div 
        ref={sidebarRef}
        className="bg-white border-r border-gray-200 flex flex-col relative"
        style={{ width: `${sidebarWidth}px`, minWidth: '240px', maxWidth: '480px' }}
      >
        {/* Header */}
        <div className="p-4 border-b border-gray-200">
          {view === "projects" || !selectedProject ? (
            <div>
              <h2 className="text-lg font-semibold text-gray-800">My Projects</h2>
              <div className="mt-2 flex items-center space-x-2">
                <button 
                  onClick={() => setIsCreateModalOpen(true)}
                  className="flex-1 flex items-center justify-between px-3 py-2 bg-blue-50 text-blue-600 rounded-lg hover:bg-blue-100 transition-colors"
                >
                  <span className="font-medium">New Project</span>
                  <Plus className="h-4 w-4" />
                </button>
                <div className="flex items-center">
                  <VoiceRecordButton onRecordingComplete={handleRecordingComplete} />
                  {isPlaying && <DotsAnimation />}
                </div>
              </div>
            </div>
          ) : (
            <div>
              <h2 className="text-lg font-semibold text-gray-800">{selectedProject.title}</h2>
              <div className="mt-2 space-y-1">
                <div className="flex items-center text-sm text-gray-600">
                  <Calendar className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span>
                    {formatDate(selectedProject.start_date)} - {formatDate(selectedProject.end_date)}
                  </span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Clock className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span>{selectedProject.weekly_commitment_hours || "N/A"}</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <Target className="h-4 w-4 mr-2 flex-shrink-0" />
                  <span>{selectedProject.difficulty_level || "N/A"}</span>
                </div>
                <div className="flex items-center text-sm text-gray-600">
                  <span className="inline-block h-4 w-4 mr-2 text-center font-bold text-blue-500">S</span>
                  <span>Status: {selectedProject.status || "N/A"}</span>
                </div>
              </div>
              <div className="mt-3">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.round(selectedProject.progress_percentage)}%` }}
                  />
                </div>
                <div className="mt-1 text-xs text-gray-600 text-right">
                  {Math.round(selectedProject.progress_percentage)}% Complete
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {view === "projects" && (
            <div className="p-2">
              {projects.length === 0 && !isLoading && (
                <p className="p-4 text-center text-gray-500">No projects found.</p>
              )}
              {projects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => selectProject(project)}
                  className="w-full p-3 mb-2 text-left bg-white border border-gray-200 rounded-lg hover:shadow-md hover:border-blue-400 transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-blue-300"
                >
                  <div className="flex items-start space-x-3">
                    <BookOpen className="h-5 w-5 text-blue-500 mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-800 truncate">{project.title}</h3>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{project.description || "No description provided."}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{project.difficulty_level || "N/A"}</span>
                        <div className="flex items-center space-x-2">
                          <div className="w-16 bg-gray-200 rounded-full h-1">
                            <div
                              className="bg-blue-500 h-1 rounded-full"
                              style={{ width: `${project.progress_percentage}%` }}
                            />
                          </div>
                          <span className="text-xs text-gray-500">{Math.round(project.progress_percentage)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {view === "milestones" && selectedProject && (
            <div>
              {selectedProject.milestones.length === 0 && (
                 <p className="p-4 text-center text-gray-500">No milestones in this project.</p>
              )}
              {selectedProject.milestones.sort((a,b) => a.order - b.order).map((milestone) => (
                <div key={milestone.id} className="py-1 border-b border-gray-100 last:border-b-0">
                  <div className="flex items-center px-4 py-2 hover:bg-gray-50 transition-colors group">
                    <button
                      onClick={() => toggleMilestone(milestone.id)}
                      className="p-1 mr-2 rounded hover:bg-gray-200"
                      aria-label={expandedMilestone === milestone.id ? "Collapse milestone" : "Expand milestone"}
                    >
                      {expandedMilestone === milestone.id ? (
                        <ChevronDown className="h-4 w-4 text-gray-600" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-600" />
                      )}
                    </button>
                    <CustomCheckbox
                      checked={completedMilestones[milestone.id] || false}
                      onChange={() => toggleMilestoneCompletion(milestone.id)}
                      size="sm"
                    />
                    <button
                      onClick={() => openMilestone(milestone)}
                      className="flex items-center flex-1 ml-2 p-1 rounded group-hover:text-blue-600"
                    >
                      <Trophy className="h-4 w-4 text-yellow-500 mr-2 flex-shrink-0" />
                      <span className="text-gray-700 text-sm text-left group-hover:text-blue-600">
                        Milestone {milestone.order}: {milestone.title}
                      </span>
                    </button>
                  </div>

                  {expandedMilestone === milestone.id && (
                    <div className="ml-8 pl-3 border-l border-gray-200">
                       {milestone.tasks.length === 0 && (
                          <p className="px-4 py-2 text-xs text-gray-500">No tasks in this milestone.</p>
                       )}
                      {milestone.tasks.map((task) => (
                        <div key={task.id} className="flex items-center px-2 py-1.5 hover:bg-gray-50 group">
                          <TaskStatusButton task={task} />
                          <button
                            onClick={() => openTask(task)}
                            className="flex items-center flex-1 ml-2 text-sm p-1 rounded group-hover:text-blue-600"
                          >
                            <FileText className="h-3.5 w-3.5 mr-2 text-gray-400 group-hover:text-blue-500 flex-shrink-0" />
                            <div className="text-left flex-1 min-w-0">
                              <div
                                className={`font-medium text-xs truncate ${
                                  completedTasks[task.id] ? "line-through text-gray-400" : "text-gray-600 group-hover:text-blue-600"
                                }`}
                                title={task.title}
                              >
                                {task.title.length > 35 ? `${task.title.substring(0, 35)}...` : task.title}
                              </div>
                              <div className="text-xs text-gray-400">Due: {formatDate(task.due_date)}</div>
                            </div>
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-200 space-y-2">
          <button 
            onClick={() => navigate('/daily-checkin')}
            className="w-full flex items-center px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Calendar className="h-4 w-4 mr-2" />
            <span>Everyday Check-in</span>
          </button>
          <button 
            onClick={logout}
            className="w-full flex items-center px-3 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <LogOut className="h-4 w-4 mr-2" />
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Resizer */}
      <div
        className={`absolute left-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-blue-500 transition-colors ${
          isResizing ? 'bg-blue-500' : 'bg-transparent'
        }`}
        style={{ left: `${sidebarWidth}px` }}
        onMouseDown={() => setIsResizing(true)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col bg-white">
        {view !== "projects" && (
          <div className="bg-gray-50 border-b border-gray-200 px-6 py-3">
            <button onClick={goBack} className="flex items-center text-sm text-blue-600 hover:text-blue-800 transition-colors font-medium">
              <ArrowLeft className="h-4 w-4 mr-1.5" />
              <span>Back</span>
            </button>
          </div>
        )}

        <div className="flex-1 p-6 lg:p-8 overflow-y-auto">
          {view === "projects" && (
            <div className="space-y-8">
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <BookOpen className="h-16 w-16 mx-auto mb-6 text-gray-300" />
                  <h2 className="text-2xl font-semibold mb-2 text-gray-700">Welcome to Your Learning Dashboard</h2>
                  <p className="text-gray-500">Select a project from the sidebar to view its details and get started.</p>
                  {projects.length === 0 && !isLoading && (
                    <p className="mt-4 text-orange-600">It looks like you don't have any projects yet. Try creating one!</p>
                  )}
                </div>
              </div>

              <div className="mt-8">
                <h2 className="text-xl font-semibold text-gray-800 mb-4">Tasks Overview</h2>
                <TasksByDateSection />
              </div>
            </div>
          )}

          {view === "milestones" && selectedProject && (
            <div className="space-y-6">
              <div>
                {editingProject?.id === selectedProject.id ? (
                  <div className="space-y-4">
                    <input
                      type="text"
                      value={editingProject.title || ''}
                      onChange={(e) => setEditingProject(prev => prev ? { ...prev, title: e.target.value } : null)}
                      className="w-full text-3xl font-bold text-gray-800 border-b border-gray-300 focus:border-blue-500 focus:outline-none pb-2"
                      placeholder="Project title"
                    />
                    <textarea
                      value={editingProject.description || ''}
                      onChange={(e) => setEditingProject(prev => prev ? { ...prev, description: e.target.value } : null)}
                      className="w-full text-gray-600 border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="Project description"
                      rows={4}
                    />
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => setEditingProject(null)}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                        disabled={isSaving}
                      >
                        Cancel
                      </button>
                      <button
                        onClick={() => updateProject(selectedProject.id, editingProject)}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                        disabled={isSaving}
                      >
                        {isSaving ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin inline" />
                            Saving...
                          </>
                        ) : (
                          'Save Changes'
                        )}
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center justify-between">
                      <h1 className="text-3xl font-bold text-gray-800">{selectedProject.title}</h1>
                      <button
                        onClick={() => setEditingProject(selectedProject)}
                        className="p-2 text-gray-500 hover:text-gray-700"
                      >
                        <Edit3 className="w-5 h-5" />
                      </button>
                    </div>
                    <p className="mt-2 text-gray-600 leading-relaxed">{selectedProject.description || "No description available for this project."}</p>
                    <div className="mt-3 text-sm text-gray-500">
                      {selectedProject.prerequisites && (
                        <p><strong>Prerequisites:</strong> {formatPrerequisites(selectedProject.prerequisites)}</p>
                      )}
                    </div>
                  </>
                )}
              </div>

              <NotesSection
                noteKey={`project-${selectedProject.id}`}
                placeholder="Add your overall notes for this project..."
              />
              
              <h2 className="text-xl font-semibold text-gray-700 pt-2">Milestones</h2>
              {selectedProject.milestones.length === 0 && (
                 <p className="p-4 text-center text-gray-500 bg-gray-50 rounded-md">This project currently has no milestones defined.</p>
              )}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {selectedProject.milestones.sort((a,b) => a.order - b.order).map((milestone) => (
                  <div
                    key={milestone.id}
                    className="bg-white p-5 rounded-lg border border-gray-200 hover:shadow-lg transition-shadow duration-200 cursor-pointer flex flex-col justify-between"
                    onClick={() => openMilestone(milestone)}
                  >
                    <div>
                      <div className="flex items-start justify-between mb-3">
                        <Trophy className="h-7 w-7 text-yellow-500" />
                        <CustomCheckbox
                          checked={completedMilestones[milestone.id] || false}
                          onChange={() => toggleMilestoneCompletion(milestone.id)}
                          size="md" // Slightly larger checkbox here
                        />
                      </div>
                      <h3 className="font-semibold text-gray-800 mb-1 text-lg">Milestone {milestone.order}: {milestone.title}</h3>
                      <p className="text-sm text-gray-600 mb-3 line-clamp-3">{milestone.description || "No description for this milestone."}</p>
                    </div>
                    <div className="text-xs text-gray-500 mt-auto">
                      {milestone.tasks.length} task{milestone.tasks.length !== 1 ? "s" : ""}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {view === "milestone" && selectedMilestone && (
            <div className="space-y-6">
              {updateError && (
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <p className="text-sm text-red-600">{updateError}</p>
                </div>
              )}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {editingMilestone?.id === selectedMilestone.id ? (
                    <div className="space-y-4">
                      <input
                        type="text"
                        value={editingMilestone.title || ''}
                        onChange={(e) => setEditingMilestone(prev => prev ? { ...prev, title: e.target.value } : null)}
                        className="w-full text-3xl font-bold text-gray-800 border-b border-gray-300 focus:border-blue-500 focus:outline-none pb-2"
                        placeholder="Milestone title"
                      />
                      <textarea
                        value={editingMilestone.description || ''}
                        onChange={(e) => setEditingMilestone(prev => prev ? { ...prev, description: e.target.value } : null)}
                        className="w-full text-gray-600 border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Milestone description"
                        rows={4}
                      />
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => setEditingMilestone(null)}
                          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                          disabled={isSaving}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => updateMilestone(selectedMilestone.id, editingMilestone)}
                          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                          disabled={isSaving}
                        >
                          {isSaving ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin inline" />
                              Saving...
                            </>
                          ) : (
                            'Save Changes'
                          )}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-blue-600 font-medium mb-1">Milestone {selectedMilestone.order}</p>
                          <h1 className="text-3xl font-bold text-gray-800">{selectedMilestone.title}</h1>
                        </div>
                        <button
                          onClick={() => setEditingMilestone(selectedMilestone)}
                          className="p-2 text-gray-500 hover:text-gray-700"
                        >
                          <Edit3 className="w-5 h-5" />
                        </button>
                      </div>
                      <p className="mt-2 text-gray-600 leading-relaxed">{selectedMilestone.description || "No description available."}</p>
                    </>
                  )}
                </div>
                <CustomCheckbox
                  checked={completedMilestones[selectedMilestone.id] || false}
                  onChange={() => toggleMilestoneCompletion(selectedMilestone.id)}
                />
              </div>

              <NotesSection
                noteKey={`milestone-${selectedMilestone.id}`}
                placeholder="Add your notes about this milestone..."
              />

              <div className="space-y-4">
                <h2 className="text-xl font-semibold text-gray-700">Tasks ({selectedMilestone.tasks.length})</h2>
                {selectedMilestone.tasks.length === 0 && (
                  <p className="p-4 text-center text-gray-500 bg-gray-50 rounded-md">No tasks defined for this milestone.</p>
                )}
                {selectedMilestone.tasks.map((task) => (
                  <div
                    key={task.id}
                    className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow duration-150"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start space-x-3 flex-1">
                        <TaskStatusButton task={task} />
                        <button onClick={() => openTask(task)} className="text-left flex-1 group">
                          <h4
                            className={`font-medium group-hover:text-blue-600 ${
                              task.status === "completed" 
                                ? "line-through text-gray-500" 
                                : task.status === "in_progress"
                                  ? "text-blue-600"
                                  : "text-gray-800"
                            }`}
                          >
                            {task.title}
                          </h4>
                          <p className="text-xs text-gray-500 mt-1 line-clamp-2 group-hover:text-blue-500">
                            {task.description || "No description."}
                          </p>
                          <div className="mt-2 flex items-center flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                            <span>Due: {formatDate(task.due_date)}</span>
                            <span>Est: {task.estimated_hours ?? "N/A"}h</span>
                            <span
                              className={`px-2 py-0.5 rounded-full font-medium ${
                                task.priority === "high"
                                  ? "bg-red-100 text-red-700"
                                  : task.priority === "medium"
                                    ? "bg-yellow-100 text-yellow-700"
                                    : task.priority === "low"
                                      ? "bg-green-100 text-green-700"
                                      : "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {task.priority || "N/A"}
                            </span>
                            {/* Добавляем индикатор статуса */}
                            <span
                              className={`px-2 py-0.5 rounded-full font-medium text-xs ${
                                task.status === "completed"
                                  ? "bg-green-100 text-green-700"
                                  : task.status === "in_progress"
                                    ? "bg-blue-100 text-blue-700"
                                    : "bg-gray-100 text-gray-700"
                              }`}
                            >
                              {formatTaskStatus(task.status)}
                            </span>
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {view === "task" && selectedTask && (
            <div className="space-y-6 max-w-3xl mx-auto">
              {updateError && (
                <div className="bg-red-50 p-4 rounded-lg border border-red-200">
                  <p className="text-sm text-red-600">{updateError}</p>
                </div>
              )}
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {editingTask?.id === selectedTask.id ? (
                    <div className="space-y-4">
                      <input
                        type="text"
                        value={editingTask.title || ''}
                        onChange={(e) => setEditingTask(prev => prev ? { ...prev, title: e.target.value } : null)}
                        className="w-full text-3xl font-bold text-gray-800 border-b border-gray-300 focus:border-blue-500 focus:outline-none pb-2"
                        placeholder="Task title"
                      />
                      <textarea
                        value={editingTask.description || ''}
                        onChange={(e) => setEditingTask(prev => prev ? { ...prev, description: e.target.value } : null)}
                        className="w-full text-gray-600 border border-gray-300 rounded-lg p-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        placeholder="Task description"
                        rows={4}
                      />
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Due Date</label>
                          <input
                            type="datetime-local"
                            value={editingTask.due_date ? new Date(editingTask.due_date).toISOString().slice(0, 16) : ''}
                            onChange={(e) => setEditingTask(prev => prev ? { ...prev, due_date: e.target.value } : null)}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                          />
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Priority</label>
                          <select
                            value={editingTask.priority}
                            onChange={(e) => setEditingTask(prev => prev ? { ...prev, priority: e.target.value } : null)}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                          >
                            <option value="low">Low</option>
                            <option value="medium">Medium</option>
                            <option value="high">High</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-sm font-medium text-gray-700">Estimated Hours</label>
                          <input
                            type="number"
                            min="0"
                            step="0.5"
                            value={editingTask.estimated_hours || ''}
                            onChange={(e) => setEditingTask(prev => prev ? { ...prev, estimated_hours: parseFloat(e.target.value) } : null)}
                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm p-2"
                          />
                        </div>
                      </div>
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => setEditingTask(null)}
                          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                          disabled={isSaving}
                        >
                          Cancel
                        </button>
                        <button
                          onClick={() => updateTask(selectedTask.id, editingTask)}
                          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50"
                          disabled={isSaving}
                        >
                          {isSaving ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin inline" />
                              Saving...
                            </>
                          ) : (
                            'Save Changes'
                          )}
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <h1 className="text-3xl font-bold text-gray-800">{selectedTask.title}</h1>
                        <button
                          onClick={() => setEditingTask(selectedTask)}
                          className="p-2 text-gray-500 hover:text-gray-700"
                        >
                          <Edit3 className="w-5 h-5" />
                        </button>
                      </div>
                      <p className="mt-2 text-gray-600 leading-relaxed">{selectedTask.description || "No description available for this task."}</p>
                    </>
                  )}
                </div>
                <div className="flex items-center space-x-2">
                  <TaskStatusButton task={selectedTask} />
                  <button
                    onClick={() => openAdaptationModal(selectedTask.id)}
                    className="p-2 text-gray-500 hover:text-blue-600 transition-colors"
                    title="Адаптировать задачу"
                  >
                    <Settings className="w-5 h-5" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4 p-4 border rounded-lg bg-gray-50">
                <div>
                  <span className="font-medium text-gray-700 text-sm">Due Date:</span>
                  <p className="text-gray-600">{formatDate(selectedTask.due_date)}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700 text-sm">Estimated Hours:</span>
                  <p className="text-gray-600">{selectedTask.estimated_hours ?? "N/A"} hours</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700 text-sm">Priority:</span>
                  <span
                    className={`ml-2 px-3 py-0.5 rounded-full text-xs font-semibold ${
                      selectedTask.priority === "high"
                        ? "bg-red-100 text-red-800"
                        : selectedTask.priority === "medium"
                          ? "bg-yellow-100 text-yellow-800"
                          : selectedTask.priority === "low"
                            ? "bg-green-100 text-green-800"
                            : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {selectedTask.priority || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700 text-sm">Status:</span>
                  <span
                    className={`ml-2 px-3 py-0.5 rounded-full text-xs font-semibold ${
                      completedTasks[selectedTask.id]
                        ? "bg-green-100 text-green-800"
                        : inProgressTasks.some(t => t.id === selectedTask.id)
                          ? "bg-blue-100 text-blue-800"
                          : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {completedTasks[selectedTask.id] 
                      ? "Completed" 
                      : inProgressTasks.some(t => t.id === selectedTask.id)
                        ? "In Progress"
                        : "Pending"}
                  </span>
                </div>
              </div>

              {selectedTask.ai_suggestion && (
                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <h3 className="font-semibold text-blue-700 mb-2 text-sm">✨ AI Suggestion</h3>
                  <p className="text-sm text-blue-600">{selectedTask.ai_suggestion}</p>
                </div>
              )}

              <NotesSection
                noteKey={`task-${selectedTask.id}`}
                placeholder="Add your notes, progress updates, or thoughts about this task..."
              />
            </div>
          )}
        </div>
      </div>

      {/* Create Project Modal */}
      <CreateProjectModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />

      {/* Добавляем модальное окно адаптации */}
      {adaptingTaskId && (
        <TaskAdaptationModal
          isOpen={isAdaptationModalOpen}
          onClose={() => {
            setIsAdaptationModalOpen(false);
            setAdaptingTaskId(null);
          }}
          onAdapt={async (message) => {
            await handleAdaptTask(adaptingTaskId, message);
          }}
          taskTitle={selectedTask?.title || ''}
        />
      )}
    </div>
  )
}

export default Dashboard