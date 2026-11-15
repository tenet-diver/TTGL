import { notFound } from 'next/navigation';
import { taskDetail } from '@/lib/task-detail';
import { TaskView } from './task-view';
export async function TaskDetail({ id }: {
    id: string;
}) {
    try {
        return <TaskView data={await taskDetail(id)}/>;
    }
    catch (error) {
        if (error instanceof Error && error.message === 'Unknown task')
            notFound();
        throw error;
    }
}
