import { computed, reactive, ref } from 'vue';
import { ElMessage, type UploadFile } from 'element-plus';
import {
  analyzeEncounter,
  confirmExistingCat,
  createNewCat,
  getRecognitionCandidates,
  uploadEncounterImages,
} from '@/api/recognition';
import type { RecognitionAnalysis, RecognitionCandidate } from '@/types/recognition';

export function useRecognitionFlow() {
  const selectedFiles = ref<UploadFile[]>([]);
  const candidates = ref<RecognitionCandidate[]>([]);
  const analyzing = ref(false);
  const activeStep = ref(1);
  const analysis = reactive<RecognitionAnalysis>({
    confidence: 0,
    healthHints: [],
    behaviorHints: [],
    summary: '',
  });

  const topCandidate = computed(() => candidates.value[0]);

  function handleUploadChange(files: UploadFile[]) {
    selectedFiles.value = files;
    activeStep.value = files.length > 0 ? 2 : 1;
  }

  async function loadRecognitionPreview() {
    candidates.value = (await getRecognitionCandidates()).slice(0, 1);
    Object.assign(analysis, await analyzeEncounter());
  }

  async function analyzeSelectedImages() {
    if (selectedFiles.value.length === 0) {
      ElMessage.warning('请先选择至少一张图片');
      return false;
    }

    analyzing.value = true;
    try {
      const rawFiles = selectedFiles.value.map((item) => item.raw).filter(Boolean) as File[];
      const result = await uploadEncounterImages(rawFiles);
      candidates.value = result.candidates.slice(0, 1);
      Object.assign(analysis, result.analysis);
      activeStep.value = 3;
      ElMessage.success(result.detectedCount > 0 ? 'YOLO 识别完成' : '识别完成，但未检测到猫咪');
      return true;
    } finally {
      analyzing.value = false;
    }
  }

  async function confirmTopCandidate() {
    if (!topCandidate.value) {
      ElMessage.warning('暂无可确认的候选猫咪');
      return false;
    }

    await confirmExistingCat(topCandidate.value.catId);
    activeStep.value = 4;
    return true;
  }

  async function createNewCatProfile() {
    await createNewCat();
    activeStep.value = 4;
  }

  return {
    activeStep,
    analysis,
    analyzing,
    candidates,
    selectedFiles,
    topCandidate,
    analyzeSelectedImages,
    confirmTopCandidate,
    createNewCatProfile,
    handleUploadChange,
    loadRecognitionPreview,
  };
}
