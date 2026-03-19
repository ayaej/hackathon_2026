import { generateToken, authenticateJWT, requireRole, MetricsCollector } from '../../src/middlewares/auth.middleware';
import { JWTPayload } from '../../src/types';
import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';

jest.mock('jsonwebtoken');
jest.mock('../../src/config/env', () => ({
  serverConfig: {
    jwtSecret: 'test-secret',
    jwtExpiresIn: '1h'
  }
}));

describe('Auth Middleware', () => {
  describe('generateToken', () => {
    it('devrait générer un token JWT valide', () => {
      const payload: JWTPayload = {
        userId: '123',
        role: 'admin',
        email: 'admin@test.com'
      };

      (jwt.sign as jest.Mock).mockReturnValue('mock-token');

      const token = generateToken(payload);

      expect(token).toBe('mock-token');
      expect(jwt.sign).toHaveBeenCalledWith(
        payload,
        'test-secret',
        { expiresIn: '1h' }
      );
    });
  });

  describe('authenticateJWT', () => {
    it('devrait autoriser un token valide', () => {
      const mockPayload: JWTPayload = {
        userId: '123',
        role: 'user',
        email: 'user@test.com'
      };

      (jwt.verify as jest.Mock).mockReturnValue(mockPayload);

      const req = {
        headers: { authorization: 'Bearer valid-token' }
      } as any;
      const res = {} as Response;
      const next = jest.fn();

      authenticateJWT(req, res, next);

      expect(req.user).toEqual(mockPayload);
      expect(next).toHaveBeenCalled();
    });

    it('devrait rejeter une requête sans token', () => {
      const req = { headers: {} } as any;
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      } as any;
      const next = jest.fn();

      authenticateJWT(req, res, next);

      expect(res.status).toHaveBeenCalledWith(401);
      expect(res.json).toHaveBeenCalledWith({ error: 'Token d\'authentification manquant' });
    });

    it('devrait rejeter un token invalide', () => {
      (jwt.verify as jest.Mock).mockImplementation(() => {
        throw new Error('Invalid token');
      });

      const req = {
        headers: { authorization: 'Bearer invalid-token' }
      } as any;
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      } as any;
      const next = jest.fn();

      authenticateJWT(req, res, next);

      expect(res.status).toHaveBeenCalledWith(403);
      expect(res.json).toHaveBeenCalledWith({ error: 'Token invalide ou expiré' });
    });
  });

  describe('requireRole', () => {
    it('devrait autoriser un utilisateur avec le bon rôle', () => {
      const middleware = requireRole('admin');
      const req = {
        user: { userId: '123', role: 'admin', email: 'admin@test.com' }
      } as any;
      const res = {} as Response;
      const next = jest.fn();

      middleware(req, res, next);

      expect(next).toHaveBeenCalled();
    });

    it('devrait rejeter un utilisateur sans le bon rôle', () => {
      const middleware = requireRole('admin');
      const req = {
        user: { userId: '123', role: 'user', email: 'user@test.com' }
      } as any;
      const res = {
        status: jest.fn().mockReturnThis(),
        json: jest.fn()
      } as any;
      const next = jest.fn();

      middleware(req, res, next);

      expect(res.status).toHaveBeenCalledWith(403);
      expect(res.json).toHaveBeenCalledWith({ error: 'Permissions insuffisantes' });
    });
  });

  describe('MetricsCollector', () => {
    it('devrait collecter les métriques des requêtes', (done) => {
      const collector = new MetricsCollector();
      const req = {
        method: 'GET',
        path: '/api/test',
        route: { path: '/api/test' }
      } as any;
      const res = {
        statusCode: 200,
        on: jest.fn((event, callback) => {
          if (event === 'finish') {
            callback();
            
            const metrics = collector.getMetrics();
            expect(metrics.totalRequests).toBe(1);
            expect(metrics.requestsByEndpoint['GET /api/test']).toBe(1);
            expect(metrics.requestsByStatus[200]).toBe(1);
            done();
          }
        })
      } as any;
      const next = jest.fn();

      collector.middleware(req, res, next);
      expect(next).toHaveBeenCalled();
    });

    it('devrait calculer le taux d\'erreur', (done) => {
      const collector = new MetricsCollector();
      
      // Simuler 2 requêtes: 1 succès, 1 erreur
      const createReq = (statusCode: number) => {
        const req = { method: 'GET', path: '/test', route: { path: '/test' } } as any;
        const res = {
          statusCode,
          on: jest.fn((event, callback) => {
            if (event === 'finish') callback();
          })
        } as any;
        const next = jest.fn();
        
        collector.middleware(req, res, next);
        // Déclencher le finish manuellement
        (res.on as jest.Mock).mock.calls[0][1]();
      };

      createReq(200); // Succès
      createReq(500); // Erreur

      setTimeout(() => {
        const metrics = collector.getMetrics();
        expect(metrics.totalRequests).toBe(2);
        expect(metrics.errorRate).toBe(50); // 1 erreur sur 2 requêtes = 50%
        done();
      }, 10);
    });
  });
});
