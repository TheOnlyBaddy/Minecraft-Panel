import React, { useState } from 'react';
import { Shield } from 'lucide-react';

interface LogoProps {
  className?: string; // Image class styling
  fallbackIconClassName?: string; // Fallback SVG class styling
  containerClassName?: string; // Optional background card wrapper class styling
}

const Logo: React.FC<LogoProps> = ({ 
  className = "w-8 h-8 object-contain", 
  fallbackIconClassName = "w-8 h-8 text-white", 
  containerClassName
}) => {
  const [imgError, setImgError] = useState(false);

  const renderContent = () => {
    if (!imgError) {
      return (
        <img 
          src="/logo.png" 
          alt="Server Logo" 
          className={className} 
          onError={() => setImgError(true)} 
        />
      );
    }
    return <Shield className={fallbackIconClassName} />;
  };

  if (containerClassName) {
    return <div className={containerClassName}>{renderContent()}</div>;
  }

  return renderContent();
};

export default Logo;
