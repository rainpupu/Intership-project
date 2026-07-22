import request from '@/api/request';
import type { CloudAdoptionOrder, CreateCloudAdoptionOrderPayload } from '@/types/cloudAdoption';

interface ApiResponse<T> {
  code: number;
  message: string;
  data: T;
}

export async function createCloudAdoptionOrder(payload: CreateCloudAdoptionOrderPayload): Promise<CloudAdoptionOrder> {
  const response = await request.post<ApiResponse<CloudAdoptionOrder>, ApiResponse<CloudAdoptionOrder>>('/cloud-adoptions', payload);
  return response.data;
}

export async function getCloudAdoptionOrders(): Promise<CloudAdoptionOrder[]> {
  const response = await request.get<ApiResponse<CloudAdoptionOrder[]>, ApiResponse<CloudAdoptionOrder[]>>('/cloud-adoptions');
  return response.data;
}
