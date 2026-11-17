import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';

export interface BloqueioConsentimentoProps {
  descricao: string;
  onIrParaConsentimentos?: () => void;
  className?: string;
  role?: string;
  'aria-live'?: 'polite' | 'assertive' | 'off';
  rotuloBotao?: string;
}

export function BloqueioConsentimento({
  descricao,
  onIrParaConsentimentos,
  className = 'flex flex-col gap-4 w-full max-w-3xl mx-auto',
  role,
  'aria-live': ariaLive,
  rotuloBotao = 'Ir para consentimentos',
}: BloqueioConsentimentoProps) {
  return (
    <div
      role={role}
      aria-live={ariaLive}
      className={className}
    >
      <Banner
        status="warning"
        title="Autorização necessária"
        description={descricao}
      />
      {onIrParaConsentimentos && (
        <div className="flex justify-start">
          <Button
            type="button"
            variant="primary"
            label={rotuloBotao}
            onClick={onIrParaConsentimentos}
          />
        </div>
      )}
    </div>
  );
}
