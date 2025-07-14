# 🎨 SYSTÈME DE DESIGN - EZBI ANALYTICS

## 🎯 PHILOSOPHIE DE DESIGN

### Vision Design
```
🧠 "Industrial Intelligence Made Beautiful"

Principes Fondamentaux:
├── Intelligence Visible: L'IA doit être perceptible et compréhensible
├── Simplicité Professionnelle: Powerful yet approachable
├── Contexte Manufacturing: Spécialisé pour l'industrie
├── Confiance Immédiate: Crédibilité et expertise transparentes
└── Performance First: Optimisé pour la productivité
```

### Personnalité de Marque
```
🎭 Brand Archetype: "The Sage" + "The Magician"

Attributs Émotionnels:
├── Expert: Deep knowledge, trusted advisor
├── Innovant: Cutting-edge technology, future-focused
├── Accessible: Complex made simple
├── Fiable: Consistent, dependable predictions
└── Français: Cultural sensitivity, local expertise

Ton de Voix:
├── Professionnel mais chaleureux
├── Confiant sans arrogance
├── Technique mais compréhensible
├── Proactif et préventif
└── Orienté résultats
```

---

## 🎨 SYSTÈME VISUEL

### Palette de Couleurs Complète

#### Couleurs Primaires - "Industrial Intelligence"
```css
/* Identité Principale */
:root {
  /* Bleu Industriel - Couleur signature */
  --ezbi-primary-50: #F0F4F8;
  --ezbi-primary-100: #D9E6F2;
  --ezbi-primary-200: #B3CCE6;
  --ezbi-primary-300: #8DB3D9;
  --ezbi-primary-400: #6799CC;
  --ezbi-primary-500: #1B365D;  /* Primary */
  --ezbi-primary-600: #152B4D;
  --ezbi-primary-700: #0F203D;
  --ezbi-primary-800: #0A152D;
  --ezbi-primary-900: #050A1D;

  /* Vert Croissance - Secondaire */
  --ezbi-secondary-50: #F0F8F4;
  --ezbi-secondary-100: #D4F1E0;
  --ezbi-secondary-200: #A9E3C2;
  --ezbi-secondary-300: #7ED4A3;
  --ezbi-secondary-400: #53C685;
  --ezbi-secondary-500: #2E8B57;  /* Secondary */
  --ezbi-secondary-600: #256F46;
  --ezbi-secondary-700: #1C5335;
  --ezbi-secondary-800: #123724;
  --ezbi-secondary-900: #091B12;

  /* Orange Alerte - Accent */
  --ezbi-accent-50: #FFF4F0;
  --ezbi-accent-100: #FFE4D6;
  --ezbi-accent-200: #FFC9AD;
  --ezbi-accent-300: #FFAE84;
  --ezbi-accent-400: #FF935B;
  --ezbi-accent-500: #FF6B35;  /* Accent */
  --ezbi-accent-600: #E55A2B;
  --ezbi-accent-700: #CC4A21;
  --ezbi-accent-800: #B23917;
  --ezbi-accent-900: #99290D;
}
```

#### Couleurs Prédictives - "Confidence Spectrum"
```css
/* Système de Confiance IA */
:root {
  /* Confiance Élevée - Vert */
  --confidence-high-50: #F0FDF4;
  --confidence-high-100: #DCFCE7;
  --confidence-high-200: #BBF7D0;
  --confidence-high-300: #86EFAC;
  --confidence-high-400: #4ADE80;
  --confidence-high-500: #22C55E;  /* 85%+ confidence */
  --confidence-high-600: #16A34A;
  --confidence-high-700: #15803D;
  --confidence-high-800: #166534;
  --confidence-high-900: #14532D;

  /* Confiance Moyenne - Orange */
  --confidence-medium-50: #FFFBEB;
  --confidence-medium-100: #FEF3C7;
  --confidence-medium-200: #FDE68A;
  --confidence-medium-300: #FCD34D;
  --confidence-medium-400: #FBBF24;
  --confidence-medium-500: #F59E0B;  /* 60-85% confidence */
  --confidence-medium-600: #D97706;
  --confidence-medium-700: #B45309;
  --confidence-medium-800: #92400E;
  --confidence-medium-900: #78350F;

  /* Confiance Faible - Rouge */
  --confidence-low-50: #FEF2F2;
  --confidence-low-100: #FEE2E2;
  --confidence-low-200: #FECACA;
  --confidence-low-300: #FCA5A5;
  --confidence-low-400: #F87171;
  --confidence-low-500: #EF4444;  /* <60% confidence */
  --confidence-low-600: #DC2626;
  --confidence-low-700: #B91C1C;
  --confidence-low-800: #991B1B;
  --confidence-low-900: #7F1D1D;
}
```

#### Couleurs Sectorielles - "Industry Identity"
```css
/* Spécialisation Manufacturing */
:root {
  /* Métallurgie - Gris Acier */
  --sector-metallurgie-50: #F8FAFC;
  --sector-metallurgie-100: #F1F5F9;
  --sector-metallurgie-200: #E2E8F0;
  --sector-metallurgie-300: #CBD5E1;
  --sector-metallurgie-400: #94A3B8;
  --sector-metallurgie-500: #607D8B;  /* Métallurgie */
  --sector-metallurgie-600: #475569;
  --sector-metallurgie-700: #334155;
  --sector-metallurgie-800: #1E293B;
  --sector-metallurgie-900: #0F172A;

  /* Plastique/Chimie - Vert Technique */
  --sector-plastique-50: #F0FDF4;
  --sector-plastique-100: #DCFCE7;
  --sector-plastique-200: #BBF7D0;
  --sector-plastique-300: #86EFAC;
  --sector-plastique-400: #4ADE80;
  --sector-plastique-500: #22C55E;  /* Plastique */
  --sector-plastique-600: #16A34A;
  --sector-plastique-700: #15803D;
  --sector-plastique-800: #166534;
  --sector-plastique-900: #14532D;

  /* Mécanique - Marron Industriel */
  --sector-mecanique-50: #FAFAF9;
  --sector-mecanique-100: #F5F5F4;
  --sector-mecanique-200: #E7E5E4;
  --sector-mecanique-300: #D6D3D1;
  --sector-mecanique-400: #A8A29E;
  --sector-mecanique-500: #795548;  /* Mécanique */
  --sector-mecanique-600: #57534E;
  --sector-mecanique-700: #44403C;
  --sector-mecanique-800: #292524;
  --sector-mecanique-900: #1C1917;

  /* Électronique - Bleu Tech */
  --sector-electronique-50: #EFF6FF;
  --sector-electronique-100: #DBEAFE;
  --sector-electronique-200: #BFDBFE;
  --sector-electronique-300: #93C5FD;
  --sector-electronique-400: #60A5FA;
  --sector-electronique-500: #3F51B5;  /* Électronique */
  --sector-electronique-600: #2563EB;
  --sector-electronique-700: #1D4ED8;
  --sector-electronique-800: #1E40AF;
  --sector-electronique-900: #1E3A8A;
}
```

#### Couleurs Neutres - "Professional Foundation"
```css
/* Base Neutre Professionnelle */
:root {
  /* Surface & Background */
  --surface-50: #FAFAFA;     /* Background principal */
  --surface-100: #F5F5F5;    /* Cards, sections */
  --surface-200: #EEEEEE;    /* Borders subtiles */
  --surface-300: #E0E0E0;    /* Dividers */
  --surface-400: #BDBDBD;    /* Disabled states */
  --surface-500: #9E9E9E;    /* Placeholders */
  --surface-600: #757575;    /* Secondary text */
  --surface-700: #616161;    /* Icons */
  --surface-800: #424242;    /* Primary text */
  --surface-900: #212121;    /* Headings */

  /* États Sémantiques */
  --success: #10B981;        /* Succès, validation */
  --warning: #F59E0B;        /* Attention, alertes */
  --error: #EF4444;          /* Erreurs, problèmes */
  --info: #3B82F6;           /* Information */
}
```

### Typography - "Professional Clarity"

#### Font Stack Optimisé
```css
/* Police Système Optimisée */
:root {
  --font-sans: 
    'Inter',                    /* Moderne, lisible */
    'SF Pro Display',           /* Apple ecosystem */
    -apple-system,              /* Native Apple */
    BlinkMacSystemFont,         /* Chrome on macOS */
    'Segoe UI',                 /* Windows */
    'Roboto',                   /* Android */
    'Oxygen',                   /* KDE */
    'Ubuntu',                   /* Ubuntu */
    'Cantarell',               /* GNOME */
    'Fira Sans',               /* Firefox OS */
    'Helvetica Neue',          /* Fallback */
    'Arial',                   /* Universal fallback */
    sans-serif;                /* System fallback */

  --font-mono: 
    'JetBrains Mono',          /* Code, data */
    'SF Mono',                 /* Apple monospace */
    'Monaco',                  /* macOS */
    'Cascadia Code',           /* Windows Terminal */
    'Ubuntu Mono',             /* Linux */
    'Courier New',             /* Universal */
    monospace;                 /* System fallback */

  --font-display:
    'Inter Display',           /* Headings, large text */
    'SF Pro Display',
    var(--font-sans);
}
```

#### Scale Typographique Harmonieuse
```css
/* Échelle Typographique Modulaire (1.25 - Major Third) */
:root {
  /* Display - Marketing, Landing */
  --text-display-xl: 4.5rem;    /* 72px - Hero titles */
  --text-display-lg: 3.75rem;   /* 60px - Section titles */
  --text-display-md: 3rem;      /* 48px - Page titles */
  --text-display-sm: 2.25rem;   /* 36px - Card titles */

  /* Headings - Interface */
  --text-h1: 2rem;              /* 32px - Dashboard titles */
  --text-h2: 1.75rem;           /* 28px - Section headers */
  --text-h3: 1.5rem;            /* 24px - Subsection headers */
  --text-h4: 1.25rem;           /* 20px - Card headers */
  --text-h5: 1.125rem;          /* 18px - List headers */
  --text-h6: 1rem;              /* 16px - Small headers */

  /* Body Text */
  --text-lg: 1.125rem;          /* 18px - Emphasized body */
  --text-base: 1rem;            /* 16px - Default body */
  --text-sm: 0.875rem;          /* 14px - Small text */
  --text-xs: 0.75rem;           /* 12px - Captions */
  --text-xxs: 0.625rem;         /* 10px - Labels */

  /* Line Heights */
  --leading-none: 1;
  --leading-tight: 1.25;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;

  /* Letter Spacing */
  --tracking-tighter: -0.05em;
  --tracking-tight: -0.025em;
  --tracking-normal: 0em;
  --tracking-wide: 0.025em;
  --tracking-wider: 0.05em;
  --tracking-widest: 0.1em;

  /* Font Weights */
  --font-thin: 100;
  --font-extralight: 200;
  --font-light: 300;
  --font-normal: 400;
  --font-medium: 500;
  --font-semibold: 600;
  --font-bold: 700;
  --font-extrabold: 800;
  --font-black: 900;
}
```

#### Classes Utilitaires Typography
```css
/* Classes Typography Prêtes à l'Emploi */

/* Display Classes */
.text-display-xl {
  font-family: var(--font-display);
  font-size: var(--text-display-xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

.text-display-lg {
  font-family: var(--font-display);
  font-size: var(--text-display-lg);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  letter-spacing: var(--tracking-tight);
}

/* Heading Classes */
.text-h1 {
  font-family: var(--font-display);
  font-size: var(--text-h1);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
  color: var(--surface-900);
}

.text-h2 {
  font-family: var(--font-display);
  font-size: var(--text-h2);
  font-weight: var(--font-semibold);
  line-height: var(--leading-snug);
  color: var(--surface-800);
}

.text-h3 {
  font-family: var(--font-sans);
  font-size: var(--text-h3);
  font-weight: var(--font-medium);
  line-height: var(--leading-snug);
  color: var(--surface-800);
}

/* Body Classes */
.text-body-lg {
  font-family: var(--font-sans);
  font-size: var(--text-lg);
  font-weight: var(--font-normal);
  line-height: var(--leading-relaxed);
  color: var(--surface-700);
}

.text-body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--surface-700);
}

.text-body-sm {
  font-family: var(--font-sans);
  font-size: var(--text-sm);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  color: var(--surface-600);
}

/* Specialty Classes */
.text-mono {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-weight: var(--font-normal);
  line-height: var(--leading-normal);
  letter-spacing: var(--tracking-wide);
}

.text-emphasis {
  font-weight: var(--font-semibold);
  color: var(--surface-900);
}

.text-muted {
  color: var(--surface-500);
}

.text-subtle {
  color: var(--surface-400);
}
```

---

## 🧩 COMPOSANTS UI SIGNATURE

### 1. Prediction Cards - Cœur EZBI

#### Structure de Base
```typescript
// 🔮 PredictionCard - Composant Signature EZBI
interface PredictionCardProps {
  title: string;
  value: number;
  currency?: string;
  confidence: number;
  trend: {
    direction: 'up' | 'down' | 'stable';
    percentage: number;
    period: string;
  };
  insight?: string;
  timeframe: string;
  onClick?: () => void;
  loading?: boolean;
  error?: string;
}

export function PredictionCard({
  title,
  value,
  currency = '€',
  confidence,
  trend,
  insight,
  timeframe,
  onClick,
  loading = false,
  error
}: PredictionCardProps) {
  const confidenceColor = getConfidenceColor(confidence);
  const trendIcon = getTrendIcon(trend.direction);
  
  return (
    <div className={cn(
      "relative overflow-hidden rounded-xl border bg-gradient-to-br p-6 transition-all duration-200",
      "hover:shadow-lg hover:scale-[1.02] cursor-pointer",
      "border-surface-200 from-surface-50 to-white",
      confidence >= 0.85 && "border-confidence-high-200 from-confidence-high-50",
      confidence >= 0.6 && confidence < 0.85 && "border-confidence-medium-200 from-confidence-medium-50",
      confidence < 0.6 && "border-confidence-low-200 from-confidence-low-50"
    )} onClick={onClick}>
      
      {/* Loading State */}
      {loading && (
        <div className="absolute inset-0 bg-white/80 flex items-center justify-center">
          <div className="flex items-center space-x-2">
            <div className="animate-spin h-5 w-5 border-2 border-primary border-t-transparent rounded-full" />
            <span className="text-sm text-surface-600">Analyse en cours...</span>
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="absolute inset-0 bg-error-50 flex items-center justify-center">
          <div className="text-center">
            <AlertTriangle className="h-8 w-8 text-error-500 mx-auto mb-2" />
            <p className="text-sm text-error-700">{error}</p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-h4 text-surface-900 mb-1">{title}</h3>
          <p className="text-sm text-surface-500">{timeframe}</p>
        </div>
        
        {/* Confidence Badge */}
        <div className={cn(
          "flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium",
          confidenceColor.bg,
          confidenceColor.text
        )}>
          <div className={cn("w-2 h-2 rounded-full", confidenceColor.dot)} />
          <span>{Math.round(confidence * 100)}%</span>
        </div>
      </div>

      {/* Value Display */}
      <div className="flex items-baseline space-x-2 mb-4">
        <span className="text-display-sm font-bold text-surface-900">
          {formatCurrency(value, currency)}
        </span>
        
        {/* Trend Indicator */}
        <div className={cn(
          "flex items-center space-x-1 px-2 py-1 rounded-full text-sm",
          trend.direction === 'up' && "bg-success-100 text-success-700",
          trend.direction === 'down' && "bg-error-100 text-error-700",
          trend.direction === 'stable' && "bg-surface-100 text-surface-700"
        )}>
          {trendIcon}
          <span className="font-medium">
            {trend.direction !== 'stable' && `${trend.percentage > 0 ? '+' : ''}${trend.percentage}%`}
            {trend.direction === 'stable' && 'Stable'}
          </span>
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-surface-500">Niveau de confiance</span>
          <span className="text-xs font-medium text-surface-700">{Math.round(confidence * 100)}%</span>
        </div>
        <div className="w-full bg-surface-200 rounded-full h-2">
          <div 
            className={cn("h-2 rounded-full transition-all duration-300", confidenceColor.bar)}
            style={{ width: `${confidence * 100}%` }}
          />
        </div>
      </div>

      {/* Insight */}
      {insight && (
        <div className="bg-surface-50 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Brain className="h-4 w-4 text-primary-500 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-surface-700">{insight}</p>
          </div>
        </div>
      )}

      {/* Hover Effect Overlay */}
      <div className="absolute inset-0 bg-gradient-to-r from-primary-500/5 to-secondary-500/5 opacity-0 hover:opacity-100 transition-opacity duration-200 pointer-events-none" />
    </div>
  );
}

// Utility Functions
function getConfidenceColor(confidence: number) {
  if (confidence >= 0.85) return {
    bg: 'bg-confidence-high-100',
    text: 'text-confidence-high-700',
    dot: 'bg-confidence-high-500',
    bar: 'bg-confidence-high-500'
  };
  
  if (confidence >= 0.6) return {
    bg: 'bg-confidence-medium-100',
    text: 'text-confidence-medium-700',
    dot: 'bg-confidence-medium-500',
    bar: 'bg-confidence-medium-500'
  };
  
  return {
    bg: 'bg-confidence-low-100',
    text: 'text-confidence-low-700',
    dot: 'bg-confidence-low-500',
    bar: 'bg-confidence-low-500'
  };
}

function getTrendIcon(direction: 'up' | 'down' | 'stable') {
  switch (direction) {
    case 'up': return <TrendingUp className="h-4 w-4" />;
    case 'down': return <TrendingDown className="h-4 w-4" />;
    case 'stable': return <Minus className="h-4 w-4" />;
  }
}

function formatCurrency(value: number, currency: string): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}
```

#### Variantes PredictionCard
```typescript
// 🎨 Variantes de PredictionCard

// Compact Variant
export function PredictionCardCompact(props: PredictionCardProps) {
  return (
    <div className="p-4 rounded-lg border border-surface-200 bg-white">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-surface-500">{props.title}</p>
          <p className="text-lg font-semibold text-surface-900">
            {formatCurrency(props.value, props.currency)}
          </p>
        </div>
        <ConfidenceBadge confidence={props.confidence} size="sm" />
      </div>
    </div>
  );
}

// Hero Variant (Dashboard principale)
export function PredictionCardHero(props: PredictionCardProps) {
  return (
    <div className="p-8 rounded-2xl bg-gradient-to-br from-primary-500 to-primary-600 text-white relative overflow-hidden">
      <div className="relative z-10">
        <h2 className="text-h2 mb-2">{props.title}</h2>
        <div className="text-display-lg font-bold mb-4">
          {formatCurrency(props.value, props.currency)}
        </div>
        <div className="flex items-center space-x-4">
          <ConfidenceBadge confidence={props.confidence} variant="dark" />
          <TrendBadge trend={props.trend} variant="dark" />
        </div>
      </div>
      
      {/* Background Pattern */}
      <div className="absolute top-0 right-0 w-64 h-64 opacity-10">
        <svg viewBox="0 0 100 100" className="w-full h-full">
          <defs>
            <pattern id="grid" width="10" height="10" patternUnits="userSpaceOnUse">
              <path d="M 10 0 L 0 0 0 10" fill="none" stroke="currentColor" strokeWidth="0.5"/>
            </pattern>
          </defs>
          <rect width="100" height="100" fill="url(#grid)" />
        </svg>
      </div>
    </div>
  );
}
```

### 2. Smart Upload Zone - Innovation UX

#### Composant Upload Avancé
```typescript
// 📤 SmartUploadZone - Upload Intelligent avec IA
interface SmartUploadZoneProps {
  onFileUpload: (files: File[]) => void;
  onProgress?: (progress: number) => void;
  onAnalysisComplete?: (analysis: FileAnalysis) => void;
  acceptedFormats: string[];
  maxFileSize: number;
  multiple?: boolean;
  disabled?: boolean;
  className?: string;
}

interface FileAnalysis {
  fileName: string;
  fileType: string;
  columnMapping: ColumnMapping[];
  dataPreview: any[];
  confidence: number;
  suggestions: string[];
}

export function SmartUploadZone({
  onFileUpload,
  onProgress,
  onAnalysisComplete,
  acceptedFormats = ['.xlsx', '.csv', '.xls'],
  maxFileSize = 50 * 1024 * 1024, // 50MB
  multiple = false,
  disabled = false,
  className
}: SmartUploadZoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [analysis, setAnalysis] = useState<FileAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { getRootProps, getInputProps, isDragActive: dragActive } = useDropzone({
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'text/csv': ['.csv']
    },
    maxSize: maxFileSize,
    multiple,
    disabled: disabled || isProcessing,
    onDrop: handleFilesDrop,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false)
  });

  async function handleFilesDrop(acceptedFiles: File[]) {
    if (acceptedFiles.length === 0) return;
    
    setError(null);
    setIsProcessing(true);
    setCurrentFile(acceptedFiles[0]);
    
    try {
      // Upload progressif
      await uploadWithProgress(acceptedFiles[0]);
      
      // Analyse IA
      await analyzeFileWithAI(acceptedFiles[0]);
      
      onFileUpload(acceptedFiles);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setIsProcessing(false);
      setUploadProgress(0);
      setAnalysisProgress(0);
    }
  }

  async function uploadWithProgress(file: File) {
    return new Promise<void>((resolve) => {
      // Simulation upload progressif
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
          resolve();
        }
        setUploadProgress(progress);
        onProgress?.(progress);
      }, 200);
    });
  }

  async function analyzeFileWithAI(file: File) {
    setAnalysisProgress(0);
    
    // Simulation analyse IA progressive
    const steps = [
      { message: "Lecture du fichier...", duration: 1000 },
      { message: "Détection des colonnes...", duration: 1500 },
      { message: "Analyse de la structure...", duration: 2000 },
      { message: "Classification des données...", duration: 1500 },
      { message: "Génération des recommandations...", duration: 1000 }
    ];

    for (let i = 0; i < steps.length; i++) {
      await new Promise(resolve => setTimeout(resolve, steps[i].duration));
      setAnalysisProgress((i + 1) / steps.length * 100);
    }

    // Mock analysis results
    const mockAnalysis: FileAnalysis = {
      fileName: file.name,
      fileType: file.type,
      columnMapping: [
        { detected: "Date", mapped: "transaction_date", confidence: 0.95 },
        { detected: "Client", mapped: "client_name", confidence: 0.88 },
        { detected: "Montant", mapped: "amount", confidence: 0.92 },
        { detected: "Statut", mapped: "status", confidence: 0.85 }
      ],
      dataPreview: [
        { Date: "2024-01-15", Client: "Metalux SARL", Montant: "15420.50", Statut: "Payé" },
        { Date: "2024-01-18", Client: "PlastiForm SAS", Montant: "8750.00", Statut: "En cours" }
      ],
      confidence: 0.90,
      suggestions: [
        "Colonnes détectées avec haute confiance",
        "Structure de données compatible",
        "Prêt pour l'analyse prédictive"
      ]
    };

    setAnalysis(mockAnalysis);
    onAnalysisComplete?.(mockAnalysis);
  }

  return (
    <div className={cn("relative", className)}>
      {/* Zone d'Upload Principale */}
      <div
        {...getRootProps()}
        className={cn(
          "relative overflow-hidden rounded-xl border-2 border-dashed transition-all duration-200",
          "min-h-[300px] flex flex-col items-center justify-center p-8 cursor-pointer",
          !isProcessing && !dragActive && "border-surface-300 bg-surface-50 hover:border-primary-400 hover:bg-primary-50",
          dragActive && "border-primary-500 bg-primary-100 scale-105",
          isProcessing && "border-surface-300 bg-surface-50 cursor-not-allowed",
          disabled && "opacity-50 cursor-not-allowed"
        )}
      >
        <input {...getInputProps()} />
        
        {/* État Normal */}
        {!isProcessing && !analysis && (
          <>
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mb-4">
                <Upload className={cn(
                  "w-8 h-8 transition-colors",
                  dragActive ? "text-primary-600" : "text-primary-500"
                )} />
              </div>
              
              <h3 className="text-h3 text-center mb-2">
                {dragActive ? "Déposez votre fichier ici" : "Importez vos données"}
              </h3>
              
              <p className="text-surface-600 text-center max-w-md">
                Glissez-déposez vos fichiers Excel ou CSV, ou cliquez pour parcourir.
                L'IA analysera automatiquement la structure de vos données.
              </p>
            </div>
            
            <div className="flex flex-wrap gap-2 justify-center mb-4">
              {acceptedFormats.map(format => (
                <span
                  key={format}
                  className="px-3 py-1 bg-surface-100 text-surface-600 rounded-full text-sm"
                >
                  {format}
                </span>
              ))}
            </div>
            
            <p className="text-xs text-surface-500 text-center">
              Taille max: {Math.round(maxFileSize / 1024 / 1024)}MB
            </p>
          </>
        )}

        {/* État Processing */}
        {isProcessing && (
          <div className="text-center w-full max-w-md">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center mb-4">
                <Brain className="w-8 h-8 text-primary-500 animate-pulse" />
              </div>
              
              <h3 className="text-h3 mb-2">Analyse en cours...</h3>
              <p className="text-surface-600 mb-6">
                {currentFile?.name}
              </p>
            </div>

            {/* Progress Upload */}
            {uploadProgress < 100 && (
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-surface-600">Upload</span>
                  <span className="text-sm font-medium">{Math.round(uploadProgress)}%</span>
                </div>
                <div className="w-full bg-surface-200 rounded-full h-2">
                  <div 
                    className="bg-primary-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Progress Analyse IA */}
            {uploadProgress >= 100 && (
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm text-surface-600">Analyse IA</span>
                  <span className="text-sm font-medium">{Math.round(analysisProgress)}%</span>
                </div>
                <div className="w-full bg-surface-200 rounded-full h-2">
                  <div 
                    className="bg-secondary-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${analysisProgress}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        )}

        {/* État Succès avec Analyse */}
        {analysis && !isProcessing && (
          <div className="text-center w-full max-w-2xl">
            <div className="mb-6">
              <div className="mx-auto w-16 h-16 rounded-full bg-success-100 flex items-center justify-center mb-4">
                <CheckCircle className="w-8 h-8 text-success-500" />
              </div>
              
              <h3 className="text-h3 mb-2">Analyse terminée !</h3>
              <p className="text-surface-600">
                Fichier analysé avec {Math.round(analysis.confidence * 100)}% de confiance
              </p>
            </div>

            {/* Aperçu de l'Analyse */}
            <div className="bg-white rounded-lg border border-surface-200 p-4 text-left">
              <h4 className="font-medium mb-3">Colonnes détectées :</h4>
              <div className="grid grid-cols-2 gap-3 mb-4">
                {analysis.columnMapping.map((col, idx) => (
                  <div key={idx} className="flex items-center justify-between p-2 bg-surface-50 rounded">
                    <span className="text-sm">{col.detected}</span>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-surface-500">→ {col.mapped}</span>
                      <div className={cn(
                        "w-2 h-2 rounded-full",
                        col.confidence > 0.9 ? "bg-success-500" :
                        col.confidence > 0.8 ? "bg-warning-500" : "bg-error-500"
                      )} />
                    </div>
                  </div>
                ))}
              </div>
              
              <div className="flex justify-between items-center">
                <span className="text-sm text-surface-600">
                  {analysis.dataPreview.length} lignes détectées
                </span>
                <button className="text-sm text-primary-600 hover:text-primary-700">
                  Voir l'aperçu →
                </button>
              </div>
            </div>
          </div>
        )}

        {/* État Erreur */}
        {error && (
          <div className="text-center w-full max-w-md">
            <div className="mx-auto w-16 h-16 rounded-full bg-error-100 flex items-center justify-center mb-4">
              <AlertTriangle className="w-8 h-8 text-error-500" />
            </div>
            <h3 className="text-h3 mb-2 text-error-700">Erreur d'analyse</h3>
            <p className="text-error-600 mb-4">{error}</p>
            <button
              onClick={() => {
                setError(null);
                setAnalysis(null);
                setCurrentFile(null);
              }}
              className="px-4 py-2 bg-error-500 text-white rounded-lg hover:bg-error-600 transition-colors"
            >
              Réessayer
            </button>
          </div>
        )}

        {/* Animation Background */}
        {dragActive && (
          <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 to-secondary-500/10 animate-pulse" />
        )}
      </div>

      {/* Suggestions IA */}
      {analysis && (
        <div className="mt-4 p-4 bg-blue-50 rounded-lg">
          <div className="flex items-start space-x-2">
            <Lightbulb className="w-5 h-5 text-blue-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-blue-900 mb-2">Recommandations IA :</h4>
              <ul className="space-y-1">
                {analysis.suggestions.map((suggestion, idx) => (
                  <li key={idx} className="text-sm text-blue-700">• {suggestion}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

Cette spécification de design system complet définit une identité visuelle unique et des composants UI innovants qui positionnent EZBI comme leader de l'IA prédictive accessible pour les PME manufacturières.