import { useEffect, useRef, useState } from 'react';
import { padraoPixels, PosicaoPonteiro } from './padraoPixels';

export interface MatrizPixelsProps {
  /** Lado de cada pixel na tela, em px CSS: a grade se ajusta ao tamanho do contêiner (pixels quadrados). */
  tamanhoCelula?: number;
  className?: string;
}

/**
 * Matriz de pixels em three.js com renderização em baixa resolução
 * ampliada via CSS com image-rendering: pixelated.
 * Paleta NOUS: Fundo #0000F2, células #000091 / #616191 / #F2F2F2.
 */
export function MatrizPixels({
  tamanhoCelula = 12,
  className = '',
}: MatrizPixelsProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [suportaWebGL, setSuportaWebGL] = useState(true);
  const [grade, setGrade] = useState({colunas: 0, linhas: 0});

  useEffect(() => {
    const container = containerRef.current;
    if (!container || typeof ResizeObserver === 'undefined') return;
    const medir = () => {
      const r = container.getBoundingClientRect();
      const colunas = Math.max(1, Math.ceil(r.width / tamanhoCelula));
      const linhas = Math.max(1, Math.ceil(r.height / tamanhoCelula));
      setGrade((g) => (g.colunas === colunas && g.linhas === linhas ? g : {colunas, linhas}));
    };
    medir();
    const observador = new ResizeObserver(medir);
    observador.observe(container);
    return () => observador.disconnect();
  }, [tamanhoCelula]);

  useEffect(() => {
    const {colunas, linhas} = grade;
    if (colunas === 0 || linhas === 0) return;
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    let animId: number | null = null;
    let renderer: any = null;
    let geometry: any = null;
    let material: any = null;
    let instancedMesh: any = null;
    let cancelado = false;

    // Detecção de prefers-reduced-motion
    const mediaQueryMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)');
    const prefereReducaoMovimento = mediaQueryMotion ? mediaQueryMotion.matches : false;

    // Estado de visibilidade
    let estaVisivel = true;
    let abaAtiva = typeof document !== 'undefined' ? document.visibilityState !== 'hidden' : true;

    // Coordenadas do ponteiro em células
    let ponteiro: PosicaoPonteiro | null = null;

    const handlePointerMove = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      const dentro = e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom;
      if (!dentro) {
        ponteiro = null;
        return;
      }
      if (rect.width > 0 && rect.height > 0) {
        const xRel = (e.clientX - rect.left) / rect.width;
        const yRel = (e.clientY - rect.top) / rect.height;
        ponteiro = {
          x: xRel * colunas,
          y: yRel * linhas,
        };
      }
    };

    const handlePointerLeave = () => {
      ponteiro = null;
    };

    // O texto do cabeçalho fica por cima do canvas: o ponteiro é lido na janela e convertido para células.
    window.addEventListener('pointermove', handlePointerMove);
    document.addEventListener('pointerleave', handlePointerLeave);

    // Carregamento sob demanda de three.js (não no bundle inicial)
    import('three')
      .then((THREE) => {
        if (cancelado) return;

        try {
          // Tenta instanciar WebGLRenderer. Em jsdom ou sem suporte, falhará no catch
          renderer = new THREE.WebGLRenderer({
            canvas,
            alpha: false,
            antialias: false,
            powerPreference: 'low-power',
          });
        } catch {
          setSuportaWebGL(false);
          return;
        }

        if (!renderer || !renderer.capabilities?.isWebGL2 && !renderer.getContext()) {
          setSuportaWebGL(false);
          return;
        }

        renderer.setSize(colunas, linhas, false);
        renderer.setClearColor(0x0000f2, 1);

        const scene = new THREE.Scene();
        const camera = new THREE.OrthographicCamera(0, colunas, linhas, 0, -1, 1);

        const totalPixels = colunas * linhas;
        geometry = new THREE.PlaneGeometry(0.88, 0.88);
        material = new THREE.MeshBasicMaterial({ color: 0xffffff, side: THREE.DoubleSide });
        instancedMesh = new THREE.InstancedMesh(geometry, material, totalPixels);

        // Configura as matrizes de cada célula na grade
        const dummy = new THREE.Object3D();
        for (let r = 0; r < linhas; r++) {
          for (let c = 0; c < colunas; c++) {
            const idx = r * colunas + c;
            // Coordenadas com y invertido para combinar com matriz CSS (topo para baixo)
            dummy.position.set(c + 0.5, linhas - (r + 0.5), 0);
            dummy.updateMatrix();
            instancedMesh.setMatrixAt(idx, dummy.matrix);
          }
        }
        instancedMesh.instanceMatrix.needsUpdate = true;
        scene.add(instancedMesh);

        // Cores NOUS
        const corFundo = new THREE.Color(0x0000f2); // #0000F2
        const corMarinho = new THREE.Color(0x000091); // #000091
        const corLinha = new THREE.Color(0x616191); // #616191
        const corPapel = new THREE.Color(0xf2f2f2); // #F2F2F2
        const corPixel = new THREE.Color();

        const atualizarCores = (tempo: number) => {
          const intensidades = padraoPixels(colunas, linhas, tempo, ponteiro);
          for (let i = 0; i < totalPixels; i++) {
            const val = intensidades[i];
            if (val <= 0.08) {
              corPixel.copy(corFundo);
            } else if (val < 0.35) {
              const t = (val - 0.08) / (0.35 - 0.08);
              corPixel.copy(corFundo).lerp(corMarinho, t);
            } else if (val < 0.65) {
              const t = (val - 0.35) / (0.65 - 0.35);
              corPixel.copy(corMarinho).lerp(corLinha, t);
            } else {
              const t = (val - 0.65) / (1.0 - 0.65);
              corPixel.copy(corLinha).lerp(corPapel, t);
            }
            instancedMesh.setColorAt(i, corPixel);
          }
          if (instancedMesh.instanceColor) {
            instancedMesh.instanceColor.needsUpdate = true;
          }
          renderer.render(scene, camera);
        };

        // Se o usuário prefere redução de movimento, desenha apenas um quadro estático
        if (prefereReducaoMovimento) {
          atualizarCores(0);
          return;
        }

        // Loop de animação limitado a ~30 fps
        let ultimoTempo = performance.now();
        const intervaloFrame = 1000 / 30; // ~33.3ms
        let tempoAcumulado = 0;

        const loop = (tempoAgora: number) => {
          if (cancelado) return;
          animId = requestAnimationFrame(loop);

          if (!estaVisivel || !abaAtiva) return;

          const delta = tempoAgora - ultimoTempo;
          if (delta >= intervaloFrame) {
            ultimoTempo = tempoAgora - (delta % intervaloFrame);
            tempoAcumulado += delta * 0.001; // segundos
            atualizarCores(tempoAcumulado);
          }
        };

        animId = requestAnimationFrame(loop);
      })
      .catch(() => {
        setSuportaWebGL(false);
      });

    // Pausar com IntersectionObserver quando fora da tela
    let observer: IntersectionObserver | null = null;
    if (typeof IntersectionObserver !== 'undefined') {
      observer = new IntersectionObserver(
        (entries) => {
          for (const entry of entries) {
            estaVisivel = entry.isIntersecting;
          }
        },
        { threshold: 0.05 }
      );
      observer.observe(container);
    }

    // Pausar com visibilityState
    const handleVisibilityChange = () => {
      abaAtiva = document.visibilityState !== 'hidden';
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      cancelado = true;
      if (animId !== null) {
        cancelAnimationFrame(animId);
      }
      window.removeEventListener('pointermove', handlePointerMove);
      document.removeEventListener('pointerleave', handlePointerLeave);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      if (observer) {
        observer.disconnect();
      }
      if (renderer) {
        try {
          renderer.dispose();
        } catch {
          // ignora
        }
      }
      if (geometry) {
        try {
          geometry.dispose();
        } catch {
          // ignora
        }
      }
      if (material) {
        try {
          material.dispose();
        } catch {
          // ignora
        }
      }
    };
  }, [grade]);

  return (
    <div
      ref={containerRef}
      role="presentation"
      aria-hidden="true"
      className={`pointer-events-auto select-none overflow-hidden ${className}`}
      style={{
        backgroundColor: '#0000F2',
      }}
    >
      {suportaWebGL ? (
        <canvas
          ref={canvasRef}
          style={{
            display: 'block',
            width: '100%',
            height: '100%',
            imageRendering: 'pixelated',
          }}
        />
      ) : (
        /* Fallback estático quando WebGL não está disponível (ex: jsdom) */
        <div
          className="w-full h-full opacity-40"
          style={{
            backgroundImage:
              'radial-gradient(circle, #616191 1px, transparent 1px)',
            backgroundSize: '8px 8px',
          }}
        />
      )}
    </div>
  );
}
