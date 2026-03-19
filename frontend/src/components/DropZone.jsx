import { useRef, useState } from 'react';
import Magnet from './ui/Magnet';

const ACCEPTED = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 'image/webp'];

export default function DropZone({ onFiles, uploading }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const validate = (files) => Array.from(files).filter((f) => ACCEPTED.includes(f.type));

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const valid = validate(e.dataTransfer.files);
    if (valid.length) onFiles(valid);
  };

  const handleChange = (e) => {
    const valid = validate(e.target.files);
    if (valid.length) onFiles(valid);
    e.target.value = '';
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`
        relative flex flex-col items-center justify-center gap-5 rounded-2xl p-14 cursor-pointer
        border-2 border-dashed transition-all duration-300 select-none
        ${dragging
          ? 'border-indigo-400 bg-indigo-500/10'
          : 'border-white/15 bg-white/3 hover:border-indigo-500/60 hover:bg-indigo-500/5'
        }
        ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onClick={() => !uploading && inputRef.current.click()}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept=".pdf,.jpg,.jpeg,.png,.tiff,.webp"
        className="hidden"
        onChange={handleChange}
        disabled={uploading}
      />

      <Magnet padding={60} magnetStrength={4} disabled={uploading}>
        <div className="w-16 h-16 rounded-2xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center backdrop-blur-sm shadow-lg shadow-indigo-500/20">
          <svg className="w-7 h-7 text-indigo-300" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
          </svg>
        </div>
      </Magnet>

      <div className="text-center">
        <p className="font-semibold text-white/80">
          {dragging ? 'Déposez vos fichiers ici' : 'Glissez-déposez vos documents'}
        </p>
        <p className="text-sm text-white/35 mt-1">ou cliquez pour sélectionner</p>
        <p className="text-xs text-white/25 mt-2">PDF, JPEG, PNG, TIFF · 20 Mo max · 10 fichiers</p>
      </div>

      {uploading && (
        <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-black/50 backdrop-blur-sm">
          <div className="flex items-center gap-2 text-indigo-300 font-medium text-sm">
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            Envoi en cours…
          </div>
        </div>
      )}
    </div>
  );
}
