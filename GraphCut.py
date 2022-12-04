import numpy as np
import pymaxflow


def get_area(scribble, area_size, img_size):
    x_min = min(scribble, key=lambda x: x[0])[0]
    x_max = max(scribble, key=lambda x: x[0])[0]
    y_min = min(scribble, key=lambda y: y[1])[1]
    y_max = max(scribble, key=lambda y: y[1])[1]

    x_left, x_right = max(0, x_min - area_size), min(img_size[0], x_max + area_size)
    y_top, y_bottom = max(0, y_min - area_size), min(img_size[1], y_max + area_size)

    return (x_left, x_right, y_top, y_bottom)


def graphcut_segment(img, fg_pixels, bg_pixels, alpha, sigma):
    eps = 1e-9
    infty = 1e9

    def create_graph(vertices_count, edges_count):
        return pymaxflow.PyGraph(vertices_count, edges_count)
        
    def add_nodes(graph, count):
        graph.add_node(count)

    def add_edges(graph, src_vertices, dst_vertices, weights, reverse_weights):
        graph.add_edge_vectorized(src_vertices, dst_vertices, weights, reverse_weights)
    
    def set_foreground_weights(graph, points, indexes_array, weight=1e10):
        indexes = indexes_array[points[:, 1], points[:, 0]].ravel()
        graph.add_tweights_vectorized(indexes, np.zeros(len(points), np.float32),
                                      np.full(len(points), weight, dtype=np.float32))
    
    def set_background_weights(graph, points, indexes_array, weight=1e10):
        indexes = indexes_array[points[:, 1], points[:, 0]].ravel()
        graph.add_tweights_vectorized(indexes, np.full(len(points), weight, dtype=np.float32),
                                      np.zeros(len(points), np.float32))
    
    def add_term_edges(graph, indexes, weights_up, weights_down):
        graph.add_tweights_vectorized(indexes, weights_up, weights_down)

    def adj_dist(v1, v2):
        diff = np.square(v1 - v2)
        dist = np.sqrt(diff[:, :, 0] + diff[:, :, 1] + diff[:, :, 2])
        return np.exp(-sigma * dist / 2)
    
    def term_weights(im, fg_pixels, bg_pixels):
        fg_hist, fg_bins = np.histogram(im[fg_pixels[:, 1], fg_pixels[:, 0]],
                                        bins=8, range=(0, 256), density=True)
        bg_hist, bg_bins = np.histogram(im[bg_pixels[:, 1], bg_pixels[:, 0]],
                                        bins=8, range=(0, 256), density=True)

        fg_ind = np.searchsorted(fg_bins[1:-1], im.flatten())
        bg_ind = np.searchsorted(bg_bins[1:-1], im.flatten())

        fg_prob = fg_hist[fg_ind] + eps
        bg_prob = bg_hist[bg_ind] + eps

        fg_weights = -np.log(fg_prob)
        bg_weights = -np.log(bg_prob)
        return fg_weights, bg_weights


    im = np.array(img) 
    im_grey = np.array(img.convert('L')) 
    im_size = im.shape[0] * im.shape[1]

    indexes = np.arange(im_size, dtype=np.int32).reshape(im.shape[:2])

    fg_pixels = np.array(fg_pixels, dtype=int) 
    bg_pixels = np.array(bg_pixels, dtype=int)

    graph = create_graph(im_size, im_size * 4)
    add_nodes(graph, im_size)

    # adjacent right
    weights = (adj_dist(im[:, 1:], im[:, :-1])).astype(np.float32).ravel()
    e1 = indexes[:, :-1].ravel()
    e2 = indexes[:, 1:].ravel()
    add_edges(graph, e1, e2, weights, 0 * weights)

    # adjacent left
    weights = (adj_dist(im[:, :-1], im[:, 1:])).astype(np.float32).ravel()
    e1 = indexes[:, 1:].ravel()
    e2 = indexes[:, :-1].ravel()
    add_edges(graph, e1, e2, 0 * weights, weights)

    # adjacent down
    weights = (adj_dist(im[1:, :], im[:-1, :])).astype(np.float32).ravel()
    e1 = indexes[:-1, :].ravel()
    e2 = indexes[1:, :].ravel()
    add_edges(graph, e1, e2, weights, 0 * weights)

    # adjacent up
    weights = (adj_dist(im[:-1, :], im[1:, :])).astype(np.float32).ravel()
    e1 = indexes[1:, :].ravel()
    e2 = indexes[:-1, :].ravel()
    add_edges(graph, e1, e2, 0 * weights, weights)
    
    
    fg_weights, bg_weights = term_weights(im_grey, fg_pixels, bg_pixels)
    add_term_edges(graph, indexes.ravel(), alpha * fg_weights.astype(np.float32).ravel(),
                                           alpha * bg_weights.astype(np.float32).ravel())

    # links to source and sink
    set_foreground_weights(graph, fg_pixels, indexes, infty)
    set_background_weights(graph, bg_pixels, indexes, infty)

    graph.maxflow()

    mask = graph.what_segment_vectorized()
    # 0 for background, 1 for object
    return mask.reshape(im.shape[:2])

def predict(img, fg_pixels, bg_pixels, last_scribble, alpha=1/20, sigma=1/10):
    area_size = 150
    x_left, x_right, y_top, y_bottom = get_area(last_scribble, area_size, img.size)
    
    new_fg_pixels = [pixel for pixel in fg_pixels if x_left <= pixel[0] < x_right and y_top <= pixel[1] < y_bottom]
    new_bg_pixels = [pixel for pixel in bg_pixels if x_left <= pixel[0] < x_right and y_top <= pixel[1] < y_bottom]

    if new_fg_pixels and new_bg_pixels:
        img_patch = img.crop((x_left, y_top, x_right, y_bottom))

        new_fg_pixels = np.array(new_fg_pixels)
        new_fg_pixels[:, 0] -= x_left
        new_fg_pixels[:, 1] -= y_top
        new_bg_pixels = np.array(new_bg_pixels)
        new_bg_pixels[:, 0] -= x_left
        new_bg_pixels[:, 1] -= y_top

        mask = graphcut_segment(img_patch, new_fg_pixels, new_bg_pixels, alpha, sigma)

        example = np.zeros((img.size[1], img.size[0])) - 1
        example[y_top:y_bottom, x_left:x_right] = mask
        return example
    else:
        return None