import { mockCats, mockRecognitionRecords } from '@/api/mock';
import type { Cat } from '@/types/cat';
import type { RecognitionRecord } from '@/types/recognition';

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
  adoptionTrend: Array<{ date: string; value: number }>;
}

export function getDashboardOverview(): Promise<DashboardOverview> {
  return Promise.resolve({
    stats: {
      totalCats: mockCats.length,
      todayRecognitions: 12,
      pendingEvents: 4,
      adoptionApplications: 8,
      adoptionOpen: mockCats.filter((cat) => cat.adoptionStatus === '待领养').length,
      focusCats: mockCats.filter((cat) => cat.isFocus).length,
    },
    recentRecognitions: mockRecognitionRecords,
    focusCats: mockCats.filter((cat) => cat.isFocus),
    adoptionTrend: [
      { date: '周一', value: 2 },
      { date: '周二', value: 3 },
      { date: '周三', value: 4 },
      { date: '周四', value: 4 },
      { date: '周五', value: 6 },
      { date: '周六', value: 7 },
      { date: '周日', value: 8 },
    ],
  });
}
