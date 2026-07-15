export type AdoptionStatus = '待领养' | '已领养' | '云领养中' | '暂不开放';

export interface Cat {
  id: string;
  code: string;
  name: string;
  coverImage: string;
  galleryImages: string[];
  coatColor: string;
  ageStage: string;
  gender: string;
  personalityTags: string[];
  healthStatus: string;
  moodStatus: string;
  adoptionStatus: AdoptionStatus;
  lastSeenLocation: string;
  lastSeenAt: string;
  description: string;
  isFocus: boolean;
}

export interface Observation {
  id: string;
  catId: string;
  location: string;
  moodStatus: string;
  healthStatus: string;
  observedAt: string;
  description: string;
}
