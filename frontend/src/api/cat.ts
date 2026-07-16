import { mockResolve } from '@/api/request';
import { mockCats, mockObservations } from '@/mock';
import type { Cat, Observation } from '@/types/cat';

export function getCatList(): Promise<Cat[]> {
  return mockResolve(mockCats);
}

export function getCatDetail(id: string): Promise<Cat | undefined> {
  return mockResolve(mockCats.find((cat) => cat.id === id));
}

export function getCatObservations(id: string): Promise<Observation[]> {
  return mockResolve(mockObservations.filter((item) => item.catId === id));
}
