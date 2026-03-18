import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';
import { serverConfig } from '../config/env';
import { JWTPayload, AuthenticatedRequest } from '../types';

/**
 * Middleware d'authentification JWT
 */
export const authenticateJWT = (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;

  if (!authHeader) {
    return res.status(401).json({ error: 'Token d\'authentification manquant' });
  }

  const token = authHeader.split(' ')[1]; // Bearer TOKEN

  try {
    const decoded = jwt.verify(token, serverConfig.jwtSecret) as JWTPayload;
    req.user = decoded;
    next();
  } catch (error) {
    return res.status(403).json({ error: 'Token invalide ou expiré' });
  }
};

/**
 * Middleware de vérification des rôles
 */
export const requireRole = (...roles: Array<'admin' | 'user' | 'readonly'>) => {
  return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Non authentifié' });
    }

    if (!roles.includes(req.user.role)) {
      return res.status(403).json({ error: 'Permissions insuffisantes' });
    }

    next();
  };
};

/**
 * Générer un token JWT
 */
export const generateToken = (payload: JWTPayload): string => {
  return jwt.sign(payload, serverConfig.jwtSecret, {
    expiresIn: serverConfig.jwtExpiresIn
  } as jwt.SignOptions);
};

/**
 * Middleware de logging des requêtes
 */
export const requestLogger = (req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    const user = (req as AuthenticatedRequest).user ? (req as AuthenticatedRequest).user!.email : 'anonymous';
    console.log(`[${new Date().toISOString()}] ${req.method} ${req.path} - ${res.statusCode} - ${duration}ms - User: ${user}`);
  });
  
  next();
};

/**
 * Middleware de métriques (pour monitoring)
 */
interface Metrics {
  totalRequests: number;
  requestsByEndpoint: Record<string, number>;
  requestsByStatus: Record<number, number>;
  averageResponseTime: number;
  errorRate: number;
}

export class MetricsCollector {
  private metrics: Metrics = {
    totalRequests: 0,
    requestsByEndpoint: {},
    requestsByStatus: {},
    averageResponseTime: 0,
    errorRate: 0
  };

  private responseTimes: number[] = [];

  middleware = (req: Request, res: Response, next: NextFunction) => {
    const start = Date.now();

    res.on('finish', () => {
      const duration = Date.now() - start;
      
      // Incrémenter compteurs
      this.metrics.totalRequests++;
      
      // Compteur par endpoint
      const endpoint = `${req.method} ${(req as any).route?.path || req.path}`;
      this.metrics.requestsByEndpoint[endpoint] = (this.metrics.requestsByEndpoint[endpoint] || 0) + 1;
      
      // Compteur par status code
      this.metrics.requestsByStatus[res.statusCode] = (this.metrics.requestsByStatus[res.statusCode] || 0) + 1;
      
      // Temps de réponse moyen
      this.responseTimes.push(duration);
      if (this.responseTimes.length > 1000) {
        this.responseTimes.shift(); // Garder seulement les 1000 dernières
      }
      this.metrics.averageResponseTime = this.responseTimes.reduce((a, b) => a + b, 0) / this.responseTimes.length;
      
      // Taux d'erreur
      const errorCount = Object.entries(this.metrics.requestsByStatus)
        .filter(([status]) => parseInt(status) >= 400)
        .reduce((sum, [, count]) => sum + count, 0);
      this.metrics.errorRate = (errorCount / this.metrics.totalRequests) * 100;
    });

    next();
  };

  getMetrics(): Metrics {
    return { ...this.metrics };
  }

  reset(): void {
    this.metrics = {
      totalRequests: 0,
      requestsByEndpoint: {},
      requestsByStatus: {},
      averageResponseTime: 0,
      errorRate: 0
    };
    this.responseTimes = [];
  }
}
