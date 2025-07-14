'use client';

import React, { useCallback, useState, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  File,
  FileText,
  X,
  CheckCircle,
  AlertCircle,
  Loader2,
  Download,
  Eye,
  Trash2,
  BarChart3,
  Database,
  Activity
} from 'lucide-react';
import { SmartUploadZoneProps, ManufacturingData } from '@/types';
import { cn, formatBytes, getFileExtension, validateFileType, validateFileSize, parseCSV } from '@/lib/utils';
import toast from 'react-hot-toast';

interface UploadedFile {
  id: string;
  file: File;
  status: 'uploading' | 'success' | 'error' | 'processing';
  progress: number;
  data?: ManufacturingData[];
  error?: string;
}

const fileIcons = {
  csv: FileText,
  json: FileText,
  xlsx: BarChart3,
  xls: BarChart3,
  default: File,
};

const defaultAcceptedTypes = [
  'text/csv',
  'application/json',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  'application/vnd.ms-excel',
];

export function SmartUploadZone({
  onFileUpload,
  onDataParsed,
  acceptedTypes = defaultAcceptedTypes,
  maxSize = 10 * 1024 * 1024, // 10MB
  maxFiles = 5,
  autoProcess = true,
  className
}: SmartUploadZoneProps) {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [isDragActive, setIsDragActive] = useState(false);
  const processingTimeoutRef = useRef<NodeJS.Timeout>();
  
  const processFile = useCallback(async (uploadedFile: UploadedFile) => {
    try {
      setUploadedFiles(prev => 
        prev.map(f => f.id === uploadedFile.id ? { ...f, status: 'processing' } : f)
      );
      
      const { file } = uploadedFile;
      const extension = getFileExtension(file.name);
      let data: ManufacturingData[] = [];
      
      if (extension === 'csv') {
        const text = await file.text();
        const parsed = parseCSV(text);
        
        // Convert to ManufacturingData format
        data = parsed.map((row, index) => ({
          id: `${Date.now()}-${index}`,
          timestamp: new Date(row.timestamp || Date.now()),
          productionLine: row.productionLine || 'Unknown',
          batchId: row.batchId || `batch-${index}`,
          parameters: {
            temperature: parseFloat(row.temperature) || 0,
            pressure: parseFloat(row.pressure) || 0,
            humidity: parseFloat(row.humidity) || 0,
            vibration: parseFloat(row.vibration) || 0,
            speed: parseFloat(row.speed) || 0,
            ...Object.keys(row).reduce((acc, key) => {
              if (!['timestamp', 'productionLine', 'batchId'].includes(key)) {
                acc[key] = row[key];
              }
              return acc;
            }, {} as any)
          },
          qualityMetrics: {
            defectRate: parseFloat(row.defectRate) || 0,
            efficiency: parseFloat(row.efficiency) || 0,
            yield: parseFloat(row.yield) || 0,
            throughput: parseFloat(row.throughput) || 0,
          },
          sensorData: [],
          alerts: [],
          metadata: {
            operator: row.operator || 'Unknown',
            shift: row.shift || 'day',
            product: row.product || 'Unknown',
            version: '1.0',
          },
        }));
      } else if (extension === 'json') {
        const text = await file.text();
        const parsed = JSON.parse(text);
        data = Array.isArray(parsed) ? parsed : [parsed];
      } else {
        throw new Error(`Type de fichier non supporté: ${extension}`);
      }
      
      // Simulate processing delay
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));
      
      setUploadedFiles(prev => 
        prev.map(f => f.id === uploadedFile.id ? { ...f, status: 'success', data } : f)
      );
      
      onDataParsed?.(data);
      toast.success(`Fichier traité avec succès: ${data.length} enregistrements`);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Erreur de traitement';
      setUploadedFiles(prev => 
        prev.map(f => f.id === uploadedFile.id ? { ...f, status: 'error', error: errorMessage } : f)
      );
      toast.error(`Erreur lors du traitement: ${errorMessage}`);
    }
  }, [onDataParsed]);
  
  const uploadFile = useCallback(async (file: File): Promise<UploadedFile> => {
    const uploadedFile: UploadedFile = {
      id: `${Date.now()}-${Math.random()}`,
      file,
      status: 'uploading',
      progress: 0,
    };
    
    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadedFiles(prev => 
        prev.map(f => f.id === uploadedFile.id ? { 
          ...f, 
          progress: Math.min(f.progress + Math.random() * 30, 100) 
        } : f)
      );
    }, 200);
    
    setTimeout(() => {
      clearInterval(progressInterval);
      setUploadedFiles(prev => 
        prev.map(f => f.id === uploadedFile.id ? { ...f, status: 'success', progress: 100 } : f)
      );
      
      if (autoProcess) {
        processingTimeoutRef.current = setTimeout(() => {
          processFile(uploadedFile);
        }, 500);
      }
    }, 1000 + Math.random() * 1000);
    
    return uploadedFile;
  }, [autoProcess, processFile]);
  
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const validFiles = acceptedFiles.filter(file => {
      if (!validateFileType(file, acceptedTypes)) {
        toast.error(`Type de fichier non supporté: ${file.name}`);
        return false;
      }
      
      if (!validateFileSize(file, maxSize)) {
        toast.error(`Fichier trop volumineux: ${file.name} (max ${formatBytes(maxSize)})`);
        return false;
      }
      
      return true;
    });
    
    if (uploadedFiles.length + validFiles.length > maxFiles) {
      toast.error(`Trop de fichiers sélectionnés (max ${maxFiles})`);
      return;
    }
    
    const newFiles = await Promise.all(validFiles.map(uploadFile));
    setUploadedFiles(prev => [...prev, ...newFiles]);
    onFileUpload(validFiles);
  }, [acceptedTypes, maxSize, maxFiles, uploadedFiles.length, uploadFile, onFileUpload]);
  
  const { getRootProps, getInputProps, isDragActive: dropzoneIsDragActive } = useDropzone({
    onDrop,
    accept: acceptedTypes.reduce((acc, type) => ({ ...acc, [type]: [] }), {}),
    maxSize,
    maxFiles,
    multiple: true,
  });
  
  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id));
  };
  
  const processFileManually = (id: string) => {
    const file = uploadedFiles.find(f => f.id === id);
    if (file) {
      processFile(file);
    }
  };
  
  const getFileIcon = (filename: string) => {
    const extension = getFileExtension(filename);
    const Icon = fileIcons[extension as keyof typeof fileIcons] || fileIcons.default;
    return Icon;
  };
  
  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'processing':
        return <Activity className="w-4 h-4 animate-pulse text-yellow-500" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };
  
  const getStatusColor = (status: UploadedFile['status']) => {
    switch (status) {
      case 'uploading':
        return 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20';
      case 'processing':
        return 'border-yellow-200 bg-yellow-50 dark:border-yellow-800 dark:bg-yellow-900/20';
      case 'success':
        return 'border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-900/20';
      case 'error':
        return 'border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20';
      default:
        return 'border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800';
    }
  };
  
  return (
    <div className={cn('w-full', className)}>
      {/* Drop Zone */}
      <div
        {...getRootProps()}
        className={cn(
          'relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors',
          dropzoneIsDragActive
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        )}
      >
        <input {...getInputProps()} />
        
        <motion.div
          initial={{ scale: 1 }}
          animate={{ scale: dropzoneIsDragActive ? 1.05 : 1 }}
          transition={{ duration: 0.2 }}
          className="flex flex-col items-center justify-center gap-4"
        >
          <div className={cn(
            'w-16 h-16 rounded-full flex items-center justify-center',
            dropzoneIsDragActive
              ? 'bg-primary-100 dark:bg-primary-900/40'
              : 'bg-gray-100 dark:bg-gray-800'
          )}>
            <Upload className={cn(
              'w-8 h-8',
              dropzoneIsDragActive
                ? 'text-primary-600 dark:text-primary-400'
                : 'text-gray-400 dark:text-gray-500'
            )} />
          </div>
          
          <div>
            <p className={cn(
              'text-lg font-medium',
              dropzoneIsDragActive
                ? 'text-primary-600 dark:text-primary-400'
                : 'text-gray-900 dark:text-white'
            )}>
              {dropzoneIsDragActive
                ? 'Déposez les fichiers ici'
                : 'Glissez-déposez vos fichiers ici'
              }
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              ou cliquez pour sélectionner
            </p>
          </div>
          
          <div className="text-xs text-gray-500 dark:text-gray-400">
            <p>Formats supportés: CSV, JSON, Excel</p>
            <p>Taille max: {formatBytes(maxSize)} • Max {maxFiles} fichiers</p>
          </div>
        </motion.div>
      </div>
      
      {/* File List */}
      <AnimatePresence>
        {uploadedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
            className="mt-4 space-y-2"
          >
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Fichiers téléchargés ({uploadedFiles.length})
            </h3>
            
            {uploadedFiles.map((uploadedFile) => {
              const FileIcon = getFileIcon(uploadedFile.file.name);
              
              return (
                <motion.div
                  key={uploadedFile.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.2 }}
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-lg border',
                    getStatusColor(uploadedFile.status)
                  )}
                >
                  <FileIcon className="w-5 h-5 text-gray-500 dark:text-gray-400 flex-shrink-0" />
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {uploadedFile.file.name}
                      </p>
                      {getStatusIcon(uploadedFile.status)}
                    </div>
                    
                    <div className="flex items-center gap-2 mt-1">
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatBytes(uploadedFile.file.size)}
                      </p>
                      
                      {uploadedFile.data && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          • {uploadedFile.data.length} enregistrements
                        </p>
                      )}
                      
                      {uploadedFile.error && (
                        <p className="text-xs text-red-600 dark:text-red-400">
                          • {uploadedFile.error}
                        </p>
                      )}
                    </div>
                    
                    {uploadedFile.status === 'uploading' && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                          <div 
                            className="bg-blue-600 h-1.5 rounded-full transition-all duration-300"
                            style={{ width: `${uploadedFile.progress}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-1">
                    {uploadedFile.status === 'success' && !uploadedFile.data && (
                      <button
                        onClick={() => processFileManually(uploadedFile.id)}
                        className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        title="Traiter le fichier"
                      >
                        <Database className="w-4 h-4 text-gray-500" />
                      </button>
                    )}
                    
                    {uploadedFile.data && (
                      <button
                        onClick={() => {
                          // Preview data logic
                        }}
                        className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                        title="Aperçu des données"
                      >
                        <Eye className="w-4 h-4 text-gray-500" />
                      </button>
                    )}
                    
                    <button
                      onClick={() => removeFile(uploadedFile.id)}
                      className="p-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                      title="Supprimer"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}