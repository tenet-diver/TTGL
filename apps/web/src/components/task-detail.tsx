import Link from 'next/link';
import { notFound } from 'next/navigation';
import { taskDetail } from '@/lib/task-detail';
import { TaskView } from './task-view';
export async function TaskDetail({ id, subtaskId }: {
    id: string;
    subtaskId?: string;
}) {
    try {
        return <TaskView data={await taskDetail(id, subtaskId)}/>;
    }
    catch (error) {
        if (error instanceof Error && ['Unknown task', 'Unknown subtask'].includes(error.message))
            notFound();
        if (error instanceof Error && error.message.startsWith('Subtask analysis is stale'))
            return <section className="storage-error"><h1>Subtask interpretation needs an update</h1><p>The source evidence changed. Analyze the task again before opening its subtasks.</p><Link href={'/tasks/' + encodeURIComponent(id)}>Back to task</Link></section>;
        throw error;
    }
}
