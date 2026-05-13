import math
import random

from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, QPropertyAnimation, QEasingCurve, Signal, \
    QParallelAnimationGroup
from PySide6.QtGui import QColor, QPainter, QPainterPath, QVector2D
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QGraphicsObject

N = 40


class FestiveOverlay(QGraphicsView):
    toggled = Signal(bool)

    def __init__(self, parent):
        super().__init__(parent)

        self.setStyleSheet("background-color: #00000000")
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.scene = QGraphicsScene()

        self.setScene(self.scene)

        self.rng = random.Random(0)
        self.animations = []

    def trigger(self):
        for _ in range(N):
            QTimer.singleShot(self.rng.randint(100, 200), self._launch_balloon)
        for i in range(round(2*N*math.log10(self.width()*self.height()))):
            QTimer.singleShot(5 * i + self.rng.randint(50, 100), self._launch_confetti)
            # break

    def _launch_balloon(self):
        self.scene.addItem(balloon := BalloonItem(self.rng))
        x = self.rng.randint(0, self.width())
        start_pos = QPointF(x, self.height() + balloon.boundingRect().height())
        balloon.setPos(start_pos)

        end_pos = QPointF(x * (1 + .1 * self.rng.gauss(0, 1)),
                          -balloon.boundingRect().height())

        self.animations.append(animation := QPropertyAnimation(balloon, b"pos"))
        animation.setStartValue(start_pos)
        animation.setEndValue(end_pos)
        animation.setDuration(self.rng.randint(2000, 4000))
        animation.setEasingCurve(QEasingCurve.Type.InOutSine)

        def cleanup():
            self.scene.removeItem(balloon)
            self.animations.remove(animation)
        animation.finished.connect(cleanup)
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    def _launch_confetti(self):
        confetti = ConfettiItem(self.rng)

        x = self.rng.choice([-confetti.width, self.width()+confetti.width])
        self.scene.addItem(confetti)

        duration = random.randint(2000, 4000)

        start = QPointF(
            x, self.height() * self.rng.uniform(.2, .6)
        )
        angle = math.radians(self.rng.uniform(30, 60))
        speed = max(self.height(), self.width()) * self.rng.uniform(.25, .75)
        velocity = QVector2D(
            -math.copysign(1, x) * speed * math.cos(angle),
            speed * math.sin(angle))
        pos_anim = BallisticAnimation(confetti, b"pos", start, velocity)
        pos_anim.setEndValue(QPointF())
        pos_anim.setDuration(duration)
        pos_anim.setEasingCurve(QEasingCurve.Type.InQuad)

        rot_anim = QPropertyAnimation(confetti, b"rotation")
        rot_anim.setStartValue(0)
        rot_anim.setEndValue(random.uniform(180, 540))
        rot_anim.setDuration(duration)

        self.animations.append(group := QParallelAnimationGroup())
        group.addAnimation(pos_anim)
        group.addAnimation(rot_anim)

        def cleanup():
            self.scene.removeItem(confetti)
            self.animations.remove(group)
        group.finished.connect(cleanup)
        group.start(QParallelAnimationGroup.DeletionPolicy.DeleteWhenStopped)

    def resizeEvent(self, event, /):
        super().resizeEvent(event)
        self.scene.setSceneRect(self.geometry())


class CustomItem(QGraphicsObject):
    def __init__(self, rng: random.Random):
        super().__init__()
        self.color = QColor.fromHsvF(rng.random(), .5, .5)


class BalloonItem(CustomItem):
    def __init__(self, rng: random.Random):
        super().__init__(rng)
        self.radius = rng.randint(20, 40)

    def boundingRect(self):
        return QRectF(
            -self.radius, -2*self.radius,
            self.radius * 2, self.radius * 3
        )

    def paint(self, painter, option, widget = None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # painter.drawRect(self.boundingRect())

        r = self.radius

        painter.setBrush(self.color)
        painter.setPen(self.color.darker(120))
        painter.drawEllipse(QPointF(0, -r), r, r)

        # highlight
        painter.setBrush(QColor(255, 255, 255, 80))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(-.25 * r, -1.5 * r), .3 * r, .25 * r)

        # knot at bottom
        painter.setBrush(self.color.darker(130))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon([
            QPointF(-.1*r, 0),
            QPointF(+.1*r, 0),
            QPointF(0, .2*r),
        ])

        # string
        painter.setPen(QColor(100, 100, 100))
        path = QPainterPath()
        path.moveTo(0, 8)
        path.cubicTo(.2*r, .4*r, -.2*r, .6*r, 0, 1*r)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path)


class ConfettiItem(CustomItem):
    def __init__(self, rng: random.Random):
        super().__init__(rng)
        self.width = round(4 * rng.uniform(1, 2))
        self.height = rng.randint(1, 2) * self.width
        self.setRotation(rng.randint(0, 360))

    def boundingRect(self):
        return QRectF(-self.width / 2, -self.height / 2,
                      self.width, self.height)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(self.color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(self.boundingRect())


class BallisticAnimation(QPropertyAnimation):
    def __init__(self, obj, prop, start, velocity):
        super().__init__(obj, prop)
        self.start, self.velocity = start, velocity
        self.gravity = 500

    def interpolated(self, lhs, rhs, progress, /):
        t = progress * self.duration() / 1000.0

        x = self.start.x() + self.velocity.x() * t
        y = self.start.y() - self.velocity.y() * t + 0.5 * self.gravity * t * t

        return QPointF(x, y)
        return super().interpolated(lhs, rhs, progress)

