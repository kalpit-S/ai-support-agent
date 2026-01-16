import { create } from 'zustand'
import type { ToolExecution } from '@/types'

interface ToolStreamState {
  executions: ToolExecution[]
  addExecution: (exec: ToolExecution) => void
  updateExecution: (id: string, update: Partial<ToolExecution>) => void
  clearExecutions: () => void
}

export const useToolStreamStore = create<ToolStreamState>((set) => ({
  executions: [],

  addExecution: (exec) =>
    set((state) => ({
      executions: [...state.executions, exec],
    })),

  updateExecution: (id, update) =>
    set((state) => ({
      executions: state.executions.map((exec) =>
        exec.id === id ? { ...exec, ...update } : exec
      ),
    })),

  clearExecutions: () => set({ executions: [] }),
}))
