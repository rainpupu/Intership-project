import { mockCats, mockObservations } from '@/api/mock';
import type { Cat, Observation } from '@/types/cat';

export function getCatList(): Promise<Cat[]> {
  return Promise.resolve(mockCats);
}

export function getCatDetail(id: string): Promise<Cat | undefined> {
  return Promise.resolve(mockCats.find((cat) => cat.id === id));
}

export function getCatObservations(id: string): Promise<Observation[]> {
  return Promise.resolve(mockObservations.filter((item) => item.catId === id));
}
