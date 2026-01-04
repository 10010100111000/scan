import { inject, provide } from 'vue'

type ScanOverlayController = {
  open: () => void
  close: () => void
  toggle: () => void
}

const ScanOverlayKey = Symbol('ScanOverlay')

export const provideScanOverlay = (controller: ScanOverlayController) => {
  provide(ScanOverlayKey, controller)
}

export const useScanOverlay = () => {
  const controller = inject<ScanOverlayController>(ScanOverlayKey)
  if (!controller) {
    throw new Error('Scan overlay is not available.')
  }
  return controller
}
