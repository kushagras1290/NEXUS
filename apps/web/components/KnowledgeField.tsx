"use client";

import { useEffect, useRef } from "react";

type Node = { x: number; y: number; z: number; vx: number; vy: number; phase: number };

export function KnowledgeField() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let width = 0, height = 0, raf = 0, scroll = 0;
    const nodes: Node[] = Array.from({length: reduced ? 70 : 150}, (_, i) => ({
      x: Math.random(), y: Math.random(), z: Math.random(),
      vx: (Math.random() - 0.5) * 0.00012,
      vy: (Math.random() - 0.5) * 0.00012,
      phase: i * 0.61
    }));

    const resize = () => {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth; height = window.innerHeight;
      canvas.width = Math.floor(width * dpr); canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`; canvas.style.height = `${height}px`;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const onScroll = () => { scroll = Math.min(window.scrollY / Math.max(window.innerHeight * 2.6, 1), 1); };
    resize(); onScroll();
    window.addEventListener("resize", resize);
    window.addEventListener("scroll", onScroll, {passive: true});

    const frame = (time: number) => {
      ctx.clearRect(0, 0, width, height);
      const cx = width / 2, cy = height * 0.52;
      const convergence = Math.max(0, (scroll - 0.25) / 0.75);
      for (const node of nodes) {
        if (!reduced) { node.x = (node.x + node.vx + 1) % 1; node.y = (node.y + node.vy + 1) % 1; }
        const targetX = cx + Math.cos(node.phase) * (55 + node.z * 100);
        const targetY = cy + Math.sin(node.phase * 1.37) * (25 + node.z * 60);
        const rawX = node.x * width, rawY = node.y * height;
        const x = rawX * (1 - convergence) + targetX * convergence;
        const y = rawY * (1 - convergence) + targetY * convergence;
        const pulse = reduced ? 1 : 0.65 + Math.sin(time * 0.0008 + node.phase) * 0.3;
        ctx.beginPath();
        ctx.fillStyle = `rgba(196, 222, 255, ${0.12 + 0.42 * pulse * (0.4 + node.z)})`;
        ctx.arc(x, y, 0.7 + node.z * 1.4, 0, Math.PI * 2);
        ctx.fill();
      }
      if (!reduced) raf = requestAnimationFrame(frame);
    };
    frame(0);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("scroll", onScroll);
    };
  }, []);

  return <canvas ref={canvasRef} className="knowledge-field" aria-hidden="true" />;
}
