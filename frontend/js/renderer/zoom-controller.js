/**
 * ZoomController: Pinch/scroll zoom (P1 implementation).
 * P0 stub — identity transform only.
 */
class ZoomController {
  constructor(canvas) {
    this.canvas  = canvas;
    this.scale   = 1.0;
    this.offsetX = 0;
    this.offsetY = 0;
  }

  /** Apply current transform to ctx (P0: no-op). */
  applyTransform(ctx) {
    // P1: ctx.setTransform(scale, 0, 0, scale, offsetX, offsetY)
  }
}
