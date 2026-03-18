import { useRef, useState } from 'react';

const ACCEPTED = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 'image/webp'];
const ACCEPTED_EXT = '.pdf, .jpg, .jpeg, .png, .tiff, .webp';

export default function DropZone({ onFiles, uploading }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  const validate = (files) => {
    return Array.from(files).filter((f) => ACCEPTED.includes(f.type));
  };

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
      onClick={() => !uploading && inputRef.current.click()}
      className={`
        relative flex flex-col items-center justify-center gap-3
        border-2 border-dashed rounded-2xl p-12 cursor-pointer
        transition-all duration-200 select-none
        ${dragging ? 'border-brand-500 bg-brand-50 scale-[1.01]' : 'border-gray-300 bg-gray-50 hover:border-brand-500 hover:bg-brand-50'}
        ${uploading ? 'opacity-60 cursor-not-allowed' : ''}
      `}
    >
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_EXT}
        className="hidden"
        onChange={handleChange}
        disabled={uploading}
      />

      <div className="w-14 h-14 rounded-full bg-white shadow flex items-center justify-center">
        <svg className="w-7 h-7 text-brand-500" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
      </div>

      <div className="text-center">
        <p className="font-semibold text-gray-700">
          {dragging ? 'Déposez vos fichiers ici' : 'Glissez-déposez vos documents'}
        </p>
        <p className="text-sm text-gray-400 mt-1">ou cliquez pour sélectionner</p>
        <p className="text-xs text-gray-400 mt-2">PDF, JPEG, PNG, TIFF — 20 Mo max — 10 fichiers max</p>
      </div>

      {uploading && (
        <div className="absolute inset-0 flex items-center justify-center rounded-2xl bg-white/70">
          <div className="flex items-center gap-2 text-brand-500 font-medium">
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
            </svg>
            envoie en cours
          </div>
        </div>
      )}
    </div>
  );
}
