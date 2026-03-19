import { useRef } from 'react';

export default function SpotlightCard({ children, className = '', spotlightColor = 'rgba(99, 102, 241, 0.15)' }) {
  const divRef = useRef(null);

  const handleMouseMove = e => {
    const rect = divRef.current.getBoundingClientRect();
    divRef.current.style.setProperty('--mouse-x', `${e.clientX - rect.left}px`);
    divRef.current.style.setProperty('--mouse-y', `${e.clientY - rect.top}px`);
    divRef.current.style.setProperty('--spotlight-color', spotlightColor);
  };

  return (
    <div
      ref={divRef}
      onMouseMove={handleMouseMove}
      className={`spotlight-card ${className}`}
    >
      {children}
    </div>
  );
}
