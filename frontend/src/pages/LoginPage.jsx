import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

import { useAuth } from '../auth/AuthContext.jsx';
import { ApiError } from '../api/client.js';
import { BrandMark } from '../brand/BrandMark.jsx';
import FormField from '../components/ui/FormField.jsx';
import { Button } from '../components/ui/Button.jsx';

const schema = z.object({
  email: z.string().email('Ingresa un email válido'),
  password: z.string().min(1, 'Ingresa tu contraseña'),
});

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [formError, setFormError] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (values) => {
    setFormError(null);
    try {
      await login(values);
      const redirectTo = location.state?.from?.pathname || '/colmena';
      navigate(redirectTo, { replace: true });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setFormError('Email o contraseña incorrectos.');
      } else {
        setFormError('No pudimos conectar con Colmena. Intenta de nuevo.');
      }
    }
  };

  return (
    <section className="relative flex min-h-screen items-center justify-center overflow-hidden bg-hero-glow px-4 py-6 sm:px-6">
      <div className="colmena-card relative z-10 w-full max-w-md px-6 py-7 sm:px-8 sm:py-8">
        <div className="mx-auto mb-5 flex flex-col items-center gap-2">
          <BrandMark className="h-10 w-10" />
          <h1 className="text-xl font-bold text-dark">Ingresa a Colmena</h1>
          <p className="text-center text-sm text-muted">Gestiona tus proyectos, instrumentos y análisis estadísticos.</p>
        </div>

        {location.state?.justRegistered ? (
          <p className="mb-5 rounded-xl bg-emerald-50 px-4 py-3 text-center text-sm font-medium text-emerald-700">
            Cuenta creada. Ahora inicia sesión.
          </p>
        ) : null}

        <form className="flex flex-col gap-4" onSubmit={handleSubmit(onSubmit)} noValidate>
          <FormField label="Email" type="email" autoComplete="email" error={errors.email?.message} {...register('email')} />
          <FormField
            label="Contraseña"
            type="password"
            autoComplete="current-password"
            error={errors.password?.message}
            {...register('password')}
          />

          {formError ? <p className="rounded-xl bg-red-50 px-4 py-3 text-sm font-medium text-danger">{formError}</p> : null}

          <Button type="submit" variant="primary" loading={isSubmitting} className="mt-2 w-full">
            Ingresar
          </Button>
        </form>

        <p className="mt-4 text-center text-sm text-muted">
          ¿No tienes cuenta?{' '}
          <Link to="/signup" className="font-semibold text-amber hover:underline">
            Crea una aquí
          </Link>
        </p>
      </div>
    </section>
  );
}
