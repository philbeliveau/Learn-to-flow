'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Eye, EyeOff, Loader2, Mail, Lock, ArrowRight } from 'lucide-react';
import { useAuthStore } from '@/store';
import { cn } from '@/lib/utils';
import toast from 'react-hot-toast';

const loginSchema = z.object({
  email: z
    .string()
    .email('Adresse email invalide')
    .min(1, 'L\'email est requis'),
  password: z
    .string()
    .min(1, 'Le mot de passe est requis')
    .min(6, 'Le mot de passe doit contenir au moins 6 caractères'),
  remember: z.boolean().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();
  const { login, isLoading, isAuthenticated } = useAuthStore();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
      remember: false,
    },
  });

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const onSubmit = async (data: LoginFormData) => {
    try {
      await login(data.email, data.password);
      toast.success('Connexion réussie !');
      router.push('/dashboard');
    } catch (error) {
      console.error('Login error:', error);
      
      if (error instanceof Error) {
        if (error.message.includes('401')) {
          setError('password', {
            type: 'manual',
            message: 'Email ou mot de passe incorrect',
          });
        } else if (error.message.includes('429')) {
          setError('email', {
            type: 'manual',
            message: 'Trop de tentatives. Veuillez réessayer plus tard.',
          });
        } else {
          setError('email', {
            type: 'manual',
            message: 'Erreur de connexion. Veuillez réessayer.',
          });
        }
      } else {
        setError('email', {
          type: 'manual',
          message: 'Erreur inattendue. Veuillez réessayer.',
        });
      }
      
      toast.error('Erreur lors de la connexion');
    }
  };

  const togglePasswordVisibility = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className="card">
      <div className="card-body">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Connexion
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Accédez à votre tableau de bord analytique
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Email Field */}
          <div>
            <label htmlFor="email" className="form-label">
              Adresse email
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Mail className="h-5 w-5 text-gray-400" />
              </div>
              <input
                {...register('email')}
                type="email"
                id="email"
                className={cn(
                  'form-input pl-10',
                  errors.email && 'border-red-500 focus:border-red-500 focus:ring-red-500'
                )}
                placeholder="votre@email.com"
                autoComplete="email"
                disabled={isSubmitting || isLoading}
              />
            </div>
            {errors.email && (
              <p className="form-error">{errors.email.message}</p>
            )}
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="form-label">
              Mot de passe
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Lock className="h-5 w-5 text-gray-400" />
              </div>
              <input
                {...register('password')}
                type={showPassword ? 'text' : 'password'}
                id="password"
                className={cn(
                  'form-input pl-10 pr-10',
                  errors.password && 'border-red-500 focus:border-red-500 focus:ring-red-500'
                )}
                placeholder="Votre mot de passe"
                autoComplete="current-password"
                disabled={isSubmitting || isLoading}
              />
              <button
                type="button"
                onClick={togglePasswordVisibility}
                className="absolute inset-y-0 right-0 pr-3 flex items-center"
                disabled={isSubmitting || isLoading}
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                ) : (
                  <Eye className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                )}
              </button>
            </div>
            {errors.password && (
              <p className="form-error">{errors.password.message}</p>
            )}
          </div>

          {/* Remember Me & Forgot Password */}
          <div className="flex items-center justify-between">
            <label className="flex items-center">
              <input
                {...register('remember')}
                type="checkbox"
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                disabled={isSubmitting || isLoading}
              />
              <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
                Se souvenir de moi
              </span>
            </label>

            <button
              type="button"
              className="text-sm text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
              disabled={isSubmitting || isLoading}
            >
              Mot de passe oublié ?
            </button>
          </div>

          {/* Submit Button */}
          <motion.button
            type="submit"
            disabled={isSubmitting || isLoading}
            className={cn(
              'w-full btn btn-primary',
              'flex items-center justify-center gap-2',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            whileHover={{ scale: isSubmitting || isLoading ? 1 : 1.02 }}
            whileTap={{ scale: isSubmitting || isLoading ? 1 : 0.98 }}
          >
            {isSubmitting || isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Connexion...
              </>
            ) : (
              <>
                Se connecter
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </motion.button>
        </form>

        {/* Demo Credentials */}
        <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Comptes de démonstration
          </h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Admin:</span>
              <span className="text-gray-900 dark:text-white font-mono">
                admin@ezbi.com / admin123
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Analyste:</span>
              <span className="text-gray-900 dark:text-white font-mono">
                analyste@ezbi.com / analyst123
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600 dark:text-gray-400">Opérateur:</span>
              <span className="text-gray-900 dark:text-white font-mono">
                operateur@ezbi.com / operator123
              </span>
            </div>
          </div>
        </div>

        {/* Additional Links */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Pas de compte ?{' '}
            <button
              type="button"
              className="text-primary-600 hover:text-primary-500 dark:text-primary-400 dark:hover:text-primary-300 font-medium"
              onClick={() => {
                // Handle signup navigation
                toast.info('Contactez votre administrateur pour créer un compte');
              }}
            >
              Contactez l'administrateur
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}