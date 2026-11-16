import { coverTitleSize, type CoverModel } from '../../lib/cover';

export default function CoverCard({ model }: { model: CoverModel }) {
  const titleSize = coverTitleSize(model.displayTitle);
  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        display: 'flex',
        backgroundColor: '#0b1220',
        color: '#f8fafc',
        fontFamily: 'Inter',
        fontWeight: 700,
      }}
    >
      <div style={{ width: 14, backgroundColor: model.accent }} />
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          width: '100%',
          height: '100%',
          padding: '52px 64px 48px 56px',
        }}
      >
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', fontSize: 28, fontWeight: 700 }}>
            {model.brand}
            <div style={{ display: 'flex', color: model.accent }}>.</div>
          </div>
          <div
            style={{
              display: 'flex',
              border: '1px solid rgba(248,250,252,0.35)',
              borderRadius: 999,
              padding: '8px 16px',
              fontSize: 16,
              letterSpacing: 1.4,
              textTransform: 'uppercase',
              color: '#e2e8f0',
              fontWeight: 700,
            }}
          >
            {model.categoryLabel}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 28,
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 72,
                height: 72,
                borderRadius: 18,
                backgroundColor: model.accent,
                color: '#ffffff',
                fontSize: 28,
                fontWeight: 700,
                marginRight: 20,
              }}
            >
              {model.monogram}
            </div>
            <div
              style={{
                display: 'flex',
                fontSize: 26,
                color: '#dbe4f0',
                fontWeight: 700,
              }}
            >
              {model.toolLabel}
            </div>
          </div>
          <div
            style={{
              display: 'flex',
              fontSize: titleSize,
              fontWeight: 700,
              lineHeight: 1.12,
              letterSpacing: -1.2,
              maxWidth: 980,
            }}
          >
            {model.displayTitle}
          </div>
        </div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div
            style={{
              display: 'flex',
              fontSize: 20,
              color: '#94a3b8',
              fontWeight: 700,
            }}
          >
            {model.keyword}
          </div>
          <div
            style={{
              width: 120,
              height: 8,
              borderRadius: 999,
              backgroundColor: model.accent,
            }}
          />
        </div>
      </div>
    </div>
  );
}
