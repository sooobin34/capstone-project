export default function MapPreview() {
  return (
    <div style={{
      background: 'white',
      border: '0.5px solid #e0e0e0',
      borderRadius: '12px',
      padding: '16px',
    }}>
      <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>지도 미리보기</p>
      <div style={{
        height: '120px',
        background: '#f5f5f5',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        border: '0.5px solid #e0e0e0',
      }}>
        <div style={{ textAlign: 'center' }}>
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" style={{ display: 'block', margin: '0 auto 6px' }}>
            <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" fill="#aaa"/>
            <circle cx="12" cy="9" r="2.5" fill="white"/>
          </svg>
          <span style={{ fontSize: '12px', color: '#888' }}>논 3개 등록됨</span>
        </div>
      </div>
      <p style={{ fontSize: '12px', color: '#1D9E75', marginTop: '8px', cursor: 'pointer' }}>지도 보기 →</p>
    </div>
  )
}