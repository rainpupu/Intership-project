import request from '@/api/request';
import type { Cat } from '@/types/cat';
import type { RecognitionRecord } from '@/types/recognition';

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export interface DashboardOverview {
  stats: {
    totalCats: number;
    todayRecognitions: number;
    pendingEvents: number;
    adoptionApplications: number;
    adoptionOpen: number;
    focusCats: number;
  };
  recentRecognitions: RecognitionRecord[];
  focusCats: Cat[];
  recognitionTrend: Array<{ date: string; value: number }>;
}

export interface HomeStats {
  totalCats: number;
  adoptionOpen: number;
  todayRecognitions: number;
  focusCats: number;
}

export function getDashboardOverview(): Promise<DashboardOverview> {
  return request
    .get<ApiResponse<DashboardOverview>, ApiResponse<DashboardOverview>>('/dashboard/overview')
    .then((response) => response.data);
}

export function getHomeStats(): Promise<HomeStats> {
  return request
    .get<ApiResponse<HomeStats>, ApiResponse<HomeStats>>('/dashboard/home-stats')
    .then((response) => response.data);
}
