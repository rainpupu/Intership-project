export type CloudGiftCategory = 'food' | 'toy' | 'health';

export interface CloudAdoptionOrder {
  id: string;
  orderNo: string;
  catId: string;
  catName: string;
  catCode: string;
  catCoverImage: string;
  userId: string;
  supporterName: string;
  giftId: string;
  giftCategory: CloudGiftCategory;
  giftName: string;
  giftDescription: string;
  giftIcon: string;
  quantity: number;
  unitPrice: number;
  totalAmount: number;
  paymentMethod: string;
  status: string;
  createdAt: string;
}

export interface CreateCloudAdoptionOrderPayload {
  catId: string;
  giftId: string;
  giftCategory: CloudGiftCategory;
  giftName: string;
  giftDescription: string;
  giftIcon: string;
  quantity: number;
  unitPrice: number;
  paymentMethod: string;
}
